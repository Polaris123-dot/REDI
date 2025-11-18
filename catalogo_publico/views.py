from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse, Http404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Count, Prefetch, Case, When, IntegerField, Value, F
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.conf import settings
import json
import re
from datetime import datetime, timedelta
from urllib.parse import urlencode
import os

from proyectos.models import Proyecto, TipoProyecto, ProyectoAutor
from publicaciones.models import Publicacion, PublicacionProyecto
from repositorio.models import Documento, Archivo, VersionDocumento
from catalogacion.models import Categoria, Etiqueta
from busqueda.models import IndiceBusqueda
from estadisticas.models import VisitaDocumento, DescargaArchivo
from django.contrib.auth.models import User


def get_client_ip(request):
    """Obtiene la IP del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def normalize_word(word):
    """
    Normaliza una palabra para búsqueda (convierte a minúsculas y elimina acentos básicos)
    """
    if not word:
        return ''
    # Convertir a minúsculas
    word = word.lower().strip()
    # Eliminar caracteres especiales al final (excepto números)
    word = re.sub(r'[^\w\s]+$', '', word)
    return word


def get_word_variants(word):
    """
    Obtiene variantes de una palabra para búsqueda (plural/singular en español)
    Retorna una lista de variantes a buscar
    """
    if not word or len(word) < 2:
        return [word]
    
    variants = [word]
    normalized = normalize_word(word)
    
    if not normalized:
        return [word]
    
    # Reglas avanzadas de plural/singular en español
    # Palabras que terminan en 's' (probablemente plural)
    if normalized.endswith('s') and len(normalized) > 3:
        # Si termina en 'es', puede ser plural (estudiantes -> estudiante)
        if normalized.endswith('es') and len(normalized) > 4:
            # Remover 'es' para obtener singular
            singular = normalized[:-2]
            if singular:
                variants.append(singular)
            # También mantener con 's' solo
            if normalized.endswith('es'):
                variants.append(normalized[:-1])
        # Si termina solo en 's', removerla
        elif len(normalized) > 3:
            singular = normalized[:-1]
            if singular:
                variants.append(singular)
    
    # Palabras que terminan en vocal (probablemente singular)
    elif normalized[-1] in 'aeiou' and len(normalized) > 2:
        # Agregar 's' para plural
        variants.append(normalized + 's')
        # Si termina en 'ción', cambiar a 'ciones'
        if normalized.endswith('ción'):
            variants.append(normalized[:-1] + 'ones')
        # Si termina en 'sión', cambiar a 'siones'
        elif normalized.endswith('sión'):
            variants.append(normalized[:-1] + 'ones')
    
    # Palabras que terminan en consonante (probablemente singular)
    elif normalized[-1] not in 'aeiou' and len(normalized) > 3:
        # Agregar 'es' para plural
        variants.append(normalized + 'es')
        # Si termina en 'z', cambiar a 'ces'
        if normalized.endswith('z'):
            variants.append(normalized[:-1] + 'ces')
    
    # Eliminar duplicados manteniendo el orden
    seen = set()
    unique_variants = []
    for v in variants:
        v_clean = v.strip().lower()
        if v_clean and len(v_clean) > 1 and v_clean not in seen:
            seen.add(v_clean)
            unique_variants.append(v_clean)
    
    return unique_variants if unique_variants else [normalized]


def tokenize_query(query):
    """
    Tokeniza una consulta de búsqueda en palabras individuales
    """
    if not query:
        return []
    
    # Dividir por espacios y eliminar palabras vacías
    words = [w.strip() for w in query.split() if w.strip()]
    
    # Normalizar y obtener variantes
    tokens = []
    for word in words:
        normalized = normalize_word(word)
        if normalized and len(normalized) > 1:  # Ignorar palabras de 1 carácter
            variants = get_word_variants(normalized)
            tokens.extend(variants)
    
    # Eliminar duplicados manteniendo el orden
    seen = set()
    unique_tokens = []
    for token in tokens:
        if token not in seen:
            seen.add(token)
            unique_tokens.append(token)
    
    return unique_tokens


def collect_publicacion_autores(publicacion):
    """
    Obtiene los autores asociados a los proyectos de una publicación.
    Retorna una dupla (nombres, detalles) sin duplicados.
    """
    autores_nombres = []
    autores_detalles = []
    seen = set()
    
    # Intentar usar objetos prefetechados para evitar consultas adicionales
    proyectos = getattr(publicacion, '_prefetched_objects_cache', {}).get('proyectos')
    if proyectos is None:
        proyectos = publicacion.proyectos.all()
    
    for proyecto in proyectos:
        autores_qs = proyecto.autores.all()
        for autor_rel in autores_qs:
            usuario_id = getattr(autor_rel, 'usuario_id', None)
            clave = usuario_id or f"{autor_rel.get_nombre_completo()}-{autor_rel.get_afiliacion()}"
            if clave in seen:
                continue
            seen.add(clave)
            
            nombre = autor_rel.get_nombre_completo()
            autores_nombres.append(nombre)
            autores_detalles.append({
                'nombre': nombre,
                'afiliacion': autor_rel.get_afiliacion(),
                'orcid': autor_rel.get_orcid_id(),
                'email': autor_rel.get_email(),
                'usuario_id': usuario_id, # Añadir el ID del usuario
            })
    
    return autores_nombres, autores_detalles


def get_publicacion_autores(publicacion, limit=None):
    """
    Retorna la lista de nombres de autores de una publicación.
    """
    nombres, _ = collect_publicacion_autores(publicacion)
    if limit is not None:
        return nombres[:limit]
    return nombres


def get_publicacion_autores_detalle(publicacion):
    """
    Retorna información detallada de los autores de una publicación.
    """
    _, detalles = collect_publicacion_autores(publicacion)
    return detalles


def build_search_query(tokens):
    """
    Construye un Q object de Django para búsqueda compleja en Publicaciones
    Busca cada token en título, descripción, y editor
    Usa OR entre tokens (al menos uno debe coincidir) pero prioriza coincidencias múltiples
    """
    if not tokens:
        return Q()
    
    # Crear queries OR para cada token
    # Cada token debe aparecer en al menos uno de los campos
    query = Q()
    
    for token in tokens:
        # Buscar el token en múltiples campos de Publicacion:
        # - Título
        # - Descripción
        # - Nombres del editor (first_name, last_name, username)
        # - También buscar en proyectos relacionados a través de PublicacionProyecto
        token_query = (
            Q(titulo__icontains=token) |
            Q(descripcion__icontains=token) |
            Q(editor__first_name__icontains=token) |
            Q(editor__last_name__icontains=token) |
            Q(editor__username__icontains=token) |
            Q(proyectos__titulo__icontains=token) |
            Q(proyectos__resumen__icontains=token)
        )
        query |= token_query
    
    return query


def calculate_relevance_score(publicacion, tokens):
    """
    Calcula un score de relevancia para una publicación basado en los tokens de búsqueda
    Mayor score = mayor relevancia
    """
    score = 0
    titulo_lower = (publicacion.titulo or '').lower()
    descripcion_lower = (publicacion.descripcion or '').lower()
    
    # Obtener nombre del editor
    editor_text = ''
    if publicacion.editor:
        editor_text = (publicacion.editor.get_full_name() or publicacion.editor.username or '').lower()
    
    # Obtener títulos de proyectos relacionados
    proyectos_text = ' '.join([
        proyecto.titulo.lower() if proyecto.titulo else ''
        for proyecto in publicacion.proyectos.all()[:5]  # Limitar a 5 proyectos para rendimiento
    ])
    
    # Contar cuántos tokens coinciden en el título
    tokens_in_title = 0
    query_complete = ' '.join(tokens).lower()
    
    for token in tokens:
        token_lower = token.lower()
        
        # Coincidencia exacta en título (peso alto: 15 puntos)
        if token_lower in titulo_lower:
            tokens_in_title += 1
            # Si está al inicio del título, más puntos
            if titulo_lower.startswith(token_lower):
                score += 20
            # Si es una palabra completa (no parte de otra palabra)
            elif f' {token_lower} ' in f' {titulo_lower} ' or titulo_lower.endswith(f' {token_lower}'):
                score += 15
            else:
                score += 10
        
        # Coincidencia en descripción (peso medio: 5 puntos)
        if token_lower in descripcion_lower:
            score += 5
        
        # Coincidencia en editor (peso medio: 3 puntos)
        if editor_text and token_lower in editor_text:
            score += 3
        
        # Coincidencia en proyectos relacionados (peso bajo: 2 puntos)
        if proyectos_text and token_lower in proyectos_text:
            score += 2
    
    # Bonus si todas las palabras están en el título
    if tokens and tokens_in_title == len(tokens):
        score += 30
    
    # Bonus si el título completo coincide (búsqueda exacta)
    if query_complete in titulo_lower:
        score += 50
    
    # Bonus si la mayoría de palabras están en el título
    if tokens and tokens_in_title >= len(tokens) * 0.7:
        score += 15
    
    return score


def advanced_search_publicaciones(publicaciones, query):
    """
    Realiza una búsqueda avanzada en publicaciones con ranking de relevancia
    Retorna una lista de publicaciones ordenadas por relevancia
    """
    if not query or not query.strip():
        return publicaciones
    
    # Tokenizar la consulta
    tokens = tokenize_query(query)
    
    if not tokens:
        return publicaciones
    
    # Construir query de búsqueda
    search_query = build_search_query(tokens)
    
    # Aplicar filtro de búsqueda
    publicaciones_filtradas = publicaciones.filter(search_query).distinct()
    
    # Convertir a lista para calcular relevancia
    # Nota: Esto puede ser costoso con muchas publicaciones, pero es necesario para ranking preciso
    publicaciones_list = list(publicaciones_filtradas.select_related('editor').prefetch_related(
        Prefetch(
            'proyectos',
            queryset=Proyecto.objects.select_related('tipo_proyecto').prefetch_related('autores__usuario')
        ),
        'categorias',
        'etiquetas'
    ))
    
    # Calcular scores de relevancia
    publicaciones_with_scores = []
    for publicacion in publicaciones_list:
        score = calculate_relevance_score(publicacion, tokens)
        if score > 0:  # Solo incluir publicaciones con score positivo
            publicaciones_with_scores.append((publicacion, score))
    
    # Ordenar por score descendente
    publicaciones_with_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Extraer solo las publicaciones
    publicaciones_ordenadas = [p[0] for p in publicaciones_with_scores]
    
    # Si no hay resultados, retornar queryset vacío
    if not publicaciones_ordenadas:
        return publicaciones.none()
    
    # Retornar queryset ordenado por IDs
    # Usamos los IDs para mantener el orden de relevancia
    publicaciones_ordenadas_ids = [p.id for p in publicaciones_ordenadas]
    
    # Crear Case/When para preservar el orden
    # Limitamos a 1000 publicaciones para evitar problemas de rendimiento
    if len(publicaciones_ordenadas_ids) > 1000:
        publicaciones_ordenadas_ids = publicaciones_ordenadas_ids[:1000]
    
    when_conditions = [
        When(id=publicacion_id, then=Value(idx))
        for idx, publicacion_id in enumerate(publicaciones_ordenadas_ids)
    ]
    
    # Retornar queryset con el orden preservado
    return publicaciones.filter(id__in=publicaciones_ordenadas_ids).annotate(
        relevance_order=Case(*when_conditions, default=Value(999999), output_field=IntegerField())
    ).order_by('relevance_order')


def get_publicaciones_publicas():
    """Retorna el queryset de publicaciones públicas y publicadas"""
    proyectos_prefetch = Prefetch(
        'proyectos',
        queryset=Proyecto.objects.select_related(
            'tipo_proyecto'
        ).prefetch_related(
            'autores__usuario'
        )
    )
    
    return Publicacion.objects.filter(
        estado='publicada',
        visibilidad='publico'
    ).select_related(
        'editor'
    ).prefetch_related(
        proyectos_prefetch,
        'categorias',
        'etiquetas'
    )


def get_filter_options():
    """Obtiene las opciones comunes para los filtros de búsqueda pública de Publicaciones"""
    # Obtener tipos de publicación únicos de publicaciones públicas
    tipos_publicacion = Publicacion.objects.filter(
        estado='publicada',
        visibilidad='publico'
    ).values_list('tipo_publicacion', flat=True).distinct()
    
    # Crear lista de opciones de tipo de publicación
    TIPO_PUBLICACION_CHOICES = dict(Publicacion.TIPO_PUBLICACION_CHOICES)
    tipos = [
        {'id': tipo, 'nombre': TIPO_PUBLICACION_CHOICES.get(tipo, tipo)}
        for tipo in tipos_publicacion
        if tipo in TIPO_PUBLICACION_CHOICES
    ]
    # Ordenar por nombre
    tipos.sort(key=lambda x: x['nombre'])

    # Obtener categorías que tienen publicaciones públicas
    categorias = Categoria.objects.filter(
        publicaciones__estado='publicada',
        publicaciones__visibilidad='publico'
    ).distinct().order_by('nombre')

    # Obtener autores que participan en publicaciones públicas
    autores = User.objects.filter(
        autoria_proyectos__proyecto__publicaciones__estado='publicada',
        autoria_proyectos__proyecto__publicaciones__visibilidad='publico'
    ).distinct().order_by('first_name', 'last_name', 'username')

    return tipos, categorias, autores


def index(request):
    """
    Página principal pública - Muestra publicaciones destacadas/recientes
    """
    # Obtener publicaciones públicas recientes
    publicaciones_qs = get_publicaciones_publicas()
    publicaciones = publicaciones_qs.order_by('-fecha_publicacion', '-fecha_creacion')[:12]
    
    # Obtener estadísticas
    total_publicaciones = publicaciones_qs.count()
    total_autores = ProyectoAutor.objects.filter(
        proyecto__publicaciones__estado='publicada',
        proyecto__publicaciones__visibilidad='publico'
    ).values_list('usuario_id', flat=True).distinct().count()
    
    # Preparar datos para el template
    publicaciones_data = []
    for publicacion in publicaciones:
        primer_proyecto = publicacion.proyectos.first()
        titulo_display = primer_proyecto.titulo if primer_proyecto else "Publicación sin título"
        resumen_display = primer_proyecto.resumen if primer_proyecto else (publicacion.descripcion or '')
        
        editor_nombre = publicacion.editor.get_full_name() if publicacion.editor and publicacion.editor.get_full_name() else (publicacion.editor.username if publicacion.editor else 'Sin editor')
        autores_list = get_publicacion_autores(publicacion, limit=3)
        publicacion_dict = {
            'id': publicacion.id,
            'titulo': titulo_display,
            'slug': publicacion.slug,
            'resumen': resumen_display,
            'url': f'/publicacion/{publicacion.slug}/',
            'fecha_publicacion': publicacion.fecha_publicacion,  # Mantener como datetime object para el template
            'tipo_publicacion': dict(Publicacion.TIPO_PUBLICACION_CHOICES).get(publicacion.tipo_publicacion, publicacion.tipo_publicacion),
            'editor': editor_nombre,
            'autores': autores_list,
            'autor': ', '.join(autores_list) if autores_list else '',
        }
        publicaciones_data.append(publicacion_dict)
    
    context = {
        'proyectos': publicaciones_data,  # Mantener 'proyectos' para compatibilidad con template
        'proyectos_destacados': publicaciones_data[:6],
        'proyectos_recientes': publicaciones_data,
        'total_proyectos': total_publicaciones,  # Mantener 'total_proyectos' para compatibilidad
        'total_autores': total_autores,
        'titulo_pagina': 'Repositorio Digital Marelliano',
    }
    
    return render(request, 'Principal/tema2/index.html', context)


def buscar(request):
    """
    Vista de búsqueda pública con filtros y búsqueda avanzada para Publicaciones
    """
    # Obtener parámetros de búsqueda
    query = request.GET.get('q', '').strip()
    tipo_publicacion = request.GET.get('tipo', '')
    categoria_id = request.GET.get('categoria', '')
    autor_id = request.GET.get('autor', '')  # Mantener 'autor' para compatibilidad con template
    fecha_inicio = request.GET.get('fecha_inicio', '')
    fecha_fin = request.GET.get('fecha_fin', '')
    page = request.GET.get('page', 1)
    
    # Obtener publicaciones públicas
    publicaciones = get_publicaciones_publicas()
    
    # Aplicar búsqueda avanzada si hay query
    if query:
        publicaciones = advanced_search_publicaciones(publicaciones, query)
    else:
        # Si no hay búsqueda, ordenar por fecha
        publicaciones = publicaciones.order_by('-fecha_publicacion', '-fecha_creacion')
    
    # Aplicar filtros adicionales
    if tipo_publicacion:
        publicaciones = publicaciones.filter(tipo_publicacion=tipo_publicacion)
    
    if categoria_id:
        publicaciones = publicaciones.filter(categorias__id=categoria_id).distinct()
    
    if autor_id:
        publicaciones = publicaciones.filter(proyectos__autores__usuario_id=autor_id).distinct()
    
    if fecha_inicio:
        try:
            # Soporta formato fecha completa o solo año
            if len(fecha_inicio) == 4 and fecha_inicio.isdigit():
                # Solo año
                publicaciones = publicaciones.filter(fecha_publicacion__year=int(fecha_inicio))
            else:
                # Fecha completa
                fecha_inicio_obj = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
                publicaciones = publicaciones.filter(fecha_publicacion__date__gte=fecha_inicio_obj)
        except (ValueError, AttributeError):
            pass
    
    if fecha_fin:
        try:
            # Soporta formato fecha completa o solo año
            if len(fecha_fin) == 4 and fecha_fin.isdigit():
                # Solo año
                publicaciones = publicaciones.filter(fecha_publicacion__year=int(fecha_fin))
            else:
                # Fecha completa
                fecha_fin_obj = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
                publicaciones = publicaciones.filter(fecha_publicacion__date__lte=fecha_fin_obj)
        except (ValueError, AttributeError):
            pass
    
    # Si no hay búsqueda, asegurar orden por fecha
    if not query:
        publicaciones = publicaciones.order_by('-fecha_publicacion', '-fecha_creacion')
    
    # Paginación
    paginator = Paginator(publicaciones, 12)  # 12 publicaciones por página
    try:
        publicaciones_paginadas = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        publicaciones_paginadas = paginator.page(1)
    
    # Preparar datos para el template
    publicaciones_data = []
    for publicacion in publicaciones_paginadas:
        editor_nombre = publicacion.editor.get_full_name() if publicacion.editor and publicacion.editor.get_full_name() else (publicacion.editor.username if publicacion.editor else 'Sin editor')
        autores_list = get_publicacion_autores(publicacion)
        publicacion_dict = {
            'id': publicacion.id,
            'titulo': publicacion.titulo,
            'slug': publicacion.slug,
            'resumen': publicacion.descripcion or '',
            'url': f'/publicacion/{publicacion.slug}/',
            'fecha_publicacion': publicacion.fecha_publicacion,
            'fecha_publicacion_str': publicacion.fecha_publicacion.strftime('%d/%m/%Y') if publicacion.fecha_publicacion else None,
            'tipo_proyecto': dict(Publicacion.TIPO_PUBLICACION_CHOICES).get(publicacion.tipo_publicacion, publicacion.tipo_publicacion),
            'autor': ', '.join(autores_list) if autores_list else 'Sin autores',  # Mantener 'autor' para compatibilidad con template
            'autores': autores_list,
            'editor': editor_nombre,
            'tiene_documento': False,  # Las publicaciones no tienen documentos directos
            'documento_id': None,
        }
        publicaciones_data.append(publicacion_dict)
    
    # Obtener opciones para filtros
    tipos_publicacion, categorias, autores = get_filter_options()

    query_params = request.GET.copy()
    query_params.pop('page', None)
    query_string = query_params.urlencode()

    context = {
        'proyectos': publicaciones_data,  # Mantener 'proyectos' para compatibilidad con template
        'proyectos_paginados': publicaciones_paginadas,  # Mantener para compatibilidad
        'query': query,
        'selected_tipo': tipo_publicacion or '',
        'selected_categoria': categoria_id or '',
        'selected_autor': autor_id or '',  # Mantener 'selected_autor' para compatibilidad
        'fecha_inicio': fecha_inicio or '',
        'fecha_fin': fecha_fin or '',
        'tipos_proyecto': tipos_publicacion,  # Mantener 'tipos_proyecto' para compatibilidad
        'categorias': categorias,
        'autores': autores,  # Mantener 'autores' para compatibilidad
        'total_resultados': paginator.count,
        'page_obj': publicaciones_paginadas,
        'query_string': query_string,
        'titulo_pagina': f'Resultados de búsqueda: "{query}"' if query else 'Explorar publicaciones',
        'sin_resultados_mensaje': f'No se encontraron publicaciones que coincidan con "{query}". Intenta con otros términos o verifica la ortografía.' if query else 'No hay publicaciones disponibles.',
        'is_paginated': publicaciones_paginadas.has_other_pages(),
    }
    
    return render(request, 'Principal/tema2/search.html', context)


def buscar_ajax(request):
    """
    Vista AJAX para búsqueda avanzada de Publicaciones
    """
    query = request.GET.get('query', '').strip()
    fecha_inicio = request.GET.get('fecha_inicio', '')
    fecha_fin = request.GET.get('fecha_fin', '')
    autor_id = request.GET.get('autor', '')
    tipo_publicacion = request.GET.get('tema', '') or request.GET.get('tipo', '')
    categoria_id = request.GET.get('sede', '') or request.GET.get('categoria', '')
    page = int(request.GET.get('page', 1))
    per_page = 12
    
    # Obtener publicaciones públicas
    publicaciones = get_publicaciones_publicas()
    
    # Aplicar búsqueda avanzada si hay query
    if query:
        publicaciones = advanced_search_publicaciones(publicaciones, query)
    else:
        publicaciones = publicaciones.order_by('-fecha_publicacion', '-fecha_creacion')
    
    # Aplicar filtros adicionales
    if tipo_publicacion:
        publicaciones = publicaciones.filter(tipo_publicacion=tipo_publicacion)
    
    if categoria_id:
        publicaciones = publicaciones.filter(categorias__id=categoria_id).distinct()
    
    if autor_id:
        publicaciones = publicaciones.filter(proyectos__autores__usuario_id=autor_id).distinct()
    
    if fecha_inicio:
        try:
            # El formato puede ser "2024" o "2024-2025" o "2024-01-01"
            if '-' in fecha_inicio:
                partes = fecha_inicio.split('-')
                if len(partes) == 3:  # Formato fecha completa
                    fecha_inicio_obj = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
                    publicaciones = publicaciones.filter(fecha_publicacion__date__gte=fecha_inicio_obj)
                elif len(partes) == 2:  # Formato año-rango
                    año_inicio = int(partes[0])
                    publicaciones = publicaciones.filter(fecha_publicacion__year__gte=año_inicio)
                else:  # Solo año
                    año = int(fecha_inicio)
                    publicaciones = publicaciones.filter(fecha_publicacion__year=año)
            else:
                año = int(fecha_inicio)
                publicaciones = publicaciones.filter(fecha_publicacion__year=año)
        except (ValueError, AttributeError):
            pass
    
    if fecha_fin:
        try:
            if '-' in fecha_fin:
                partes = fecha_fin.split('-')
                if len(partes) == 3:  # Formato fecha completa
                    fecha_fin_obj = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
                    publicaciones = publicaciones.filter(fecha_publicacion__date__lte=fecha_fin_obj)
                elif len(partes) == 2:  # Formato año-rango
                    año_fin = int(partes[-1])
                    publicaciones = publicaciones.filter(fecha_publicacion__year__lte=año_fin)
                else:
                    año = int(fecha_fin)
                    publicaciones = publicaciones.filter(fecha_publicacion__year=año)
            else:
                año = int(fecha_fin)
                publicaciones = publicaciones.filter(fecha_publicacion__year=año)
        except (ValueError, AttributeError):
            pass
    
    # Si no hay búsqueda, asegurar orden por fecha
    if not query:
        publicaciones = publicaciones.order_by('-fecha_publicacion', '-fecha_creacion')
    
    # Paginación
    paginator = Paginator(publicaciones, per_page)
    try:
        publicaciones_paginadas = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        publicaciones_paginadas = paginator.page(1)
    
    # Preparar resultados
    resultados = []
    for publicacion in publicaciones_paginadas:
        primer_proyecto = publicacion.proyectos.first()
        titulo_display = primer_proyecto.titulo if primer_proyecto else "Publicación sin título"
        resumen_display = primer_proyecto.resumen if primer_proyecto else (publicacion.descripcion or '')
        
        editor_nombre = publicacion.editor.get_full_name() if publicacion.editor and publicacion.editor.get_full_name() else (publicacion.editor.username if publicacion.editor else 'Sin editor')
        autores_list = get_publicacion_autores(publicacion)
        resultados.append({
            'id': publicacion.id,
            'titulo': titulo_display,
            'slug': publicacion.slug,
            'resumen': resumen_display,
            'autor': ', '.join(autores_list) if autores_list else 'Sin autores',
            'autores': autores_list,
            'url': f'/publicacion/{publicacion.slug}/',
            'fecha_publicacion': publicacion.fecha_publicacion.strftime('%Y-%m-%d') if publicacion.fecha_publicacion else None,
            'tipo_proyecto': dict(Publicacion.TIPO_PUBLICACION_CHOICES).get(publicacion.tipo_publicacion, publicacion.tipo_publicacion),
        })
    
    return JsonResponse({
        'success': True,
        'resultados': resultados,
        'total': paginator.count,
        'total_pages': paginator.num_pages,
        'current_page': publicaciones_paginadas.number,
    })


def publicacion_detalle(request, slug):
    """
    Vista de detalle de una publicación pública
    Permite acceso por URL slug incluso si la publicación no está publicada
    """
    # Primero intentar obtener de publicaciones públicas
    try:
        publicacion = get_publicaciones_publicas().get(slug=slug)
    except Publicacion.DoesNotExist:
        # Si no está en publicaciones públicas, intentar obtenerla directamente
        # Esto permite acceso por URL incluso si está en borrador o es privada
        try:
            publicacion = Publicacion.objects.select_related(
                'editor'
            ).prefetch_related(
                Prefetch(
                    'proyectos',
                    queryset=Proyecto.objects.select_related(
                        'tipo_proyecto'
                    ).prefetch_related(
                        'autores__usuario'
                    )
                ),
                'categorias',
                'etiquetas'
            ).get(slug=slug)
            
            # Si no está publicada o no es pública, verificar permisos
            if publicacion.estado != 'publicada' or publicacion.visibilidad != 'publico':
                # Permitir acceso si el usuario es el editor, es superusuario, o tiene permisos
                if not request.user.is_authenticated:
                    # Si no está autenticado y la publicación no es pública, mostrar 404
                    from django.http import Http404
                    raise Http404("La publicación no está disponible públicamente")
                elif not (request.user.is_superuser or 
                         (publicacion.editor and publicacion.editor.id == request.user.id)):
                    # Si no tiene permisos, mostrar 404
                    from django.http import Http404
                    raise Http404("No tiene permisos para ver esta publicación")
        except Publicacion.DoesNotExist:
            from django.http import Http404
            raise Http404("La publicación no existe")
    
    # Obtener el primer proyecto para el título y resumen principal
    primer_proyecto = publicacion.proyectos.first()
    
    # Obtener editor
    editor_nombre = publicacion.editor.get_full_name() if publicacion.editor and publicacion.editor.get_full_name() else (publicacion.editor.username if publicacion.editor else 'Sin editor')
    
    # Obtener autores de todos los proyectos asociados
    autores_list = get_publicacion_autores(publicacion)
    autores_detalle = get_publicacion_autores_detalle(publicacion)
    if not autores_list and editor_nombre:
        autores_list = [editor_nombre]
    
    # Obtener categorías y etiquetas
    categorias = publicacion.categorias.all()
    etiquetas = publicacion.etiquetas.all()
    
    # Obtener proyectos relacionados a esta publicación (mantener como QuerySet hasta usar)
    proyectos_relacionados_qs = publicacion.proyectos.all()[:10]
    proyectos_relacionados_list = list(proyectos_relacionados_qs)
    proyectos_relacionados_data = []
    for proyecto in proyectos_relacionados_list:
        # Obtener documento del proyecto si existe
        documento_url = None
        if hasattr(proyecto, 'documento'):
            documento = proyecto.documento
            version_actual = documento.versiones.filter(es_version_actual=True).first()
            if version_actual:
                archivo_principal = version_actual.archivos.filter(es_archivo_principal=True).first()
                if not archivo_principal:
                    archivo_principal = version_actual.archivos.first()
                if archivo_principal and archivo_principal.archivo:
                    documento_url = archivo_principal.archivo.url
        
        proyectos_relacionados_data.append({
            'titulo': proyecto.titulo,
            'url': f'/publicacion/{publicacion.slug}/#proyecto-{proyecto.id}',
            'documento_url': documento_url,
            'documento_id': proyecto.documento.id if hasattr(proyecto, 'documento') and proyecto.documento else None,
            'autores': [autor_rel.get_nombre_completo() for autor_rel in proyecto.autores.all()],
        })
    
    # Obtener publicaciones relacionadas (misma categoría o tipo)
    publicaciones_relacionadas = get_publicaciones_publicas().filter(
        Q(categorias__in=categorias) | Q(tipo_publicacion=publicacion.tipo_publicacion)
    ).exclude(id=publicacion.id).distinct()[:5]
    
    publicaciones_relacionadas_data = []
    for pub_rel in publicaciones_relacionadas:
        # Usar el título del primer proyecto de la publicación relacionada
        primer_proyecto_rel = pub_rel.proyectos.first()
        titulo_rel = primer_proyecto_rel.titulo if primer_proyecto_rel else "Publicación sin título"
        publicaciones_relacionadas_data.append({
            'titulo': titulo_rel,
            'url': f'/publicacion/{pub_rel.slug}/',
        })
    
    # Documento principal (del primer proyecto)
    documento = None
    archivo_principal = None
    archivo_url = None
    documento_id = None
    if primer_proyecto and hasattr(primer_proyecto, 'documento') and primer_proyecto.documento:
        documento = primer_proyecto.documento
        documento_id = documento.id
        version_actual = documento.versiones.filter(es_version_actual=True).first()
        if version_actual:
            archivo_principal = version_actual.archivos.filter(es_archivo_principal=True).first()
            if not archivo_principal:
                archivo_principal = version_actual.archivos.first()
            if archivo_principal and archivo_principal.archivo:
                archivo_url = archivo_principal.archivo.url
    
    # Obtener comentarios públicos del documento si existe
    comentarios_data = []
    if documento:
        from interaccion.models import Comentario
        comentarios = Comentario.objects.filter(
            documento=documento,
            es_publico=True
        ).select_related('usuario').order_by('-fecha_creacion')[:50]
        
        for comentario in comentarios:
            comentarios_data.append({
                'id': comentario.id,
                'usuario_nombre': comentario.usuario.get_full_name() or comentario.usuario.username,
                'contenido': comentario.contenido,
                'fecha_creacion': comentario.fecha_creacion,
                'fecha_creacion_str': comentario.fecha_creacion.strftime('%d de %B, %Y') if comentario.fecha_creacion else '',
            })
    
    context = {
        'publicacion': publicacion,
        'titulo': primer_proyecto.titulo if primer_proyecto else "Publicación sin título",
        'resumen': primer_proyecto.resumen if primer_proyecto else (publicacion.descripcion or ''),
        'autores': autores_list,
        'autores_detalle': autores_detalle,
        'editor': editor_nombre,
        'editor_id': publicacion.editor.id if publicacion.editor else None, # Añadir editor_id
        'fecha_publicacion': publicacion.fecha_publicacion,
        'categorias': categorias,
        'etiquetas': etiquetas,
        'documento': documento,
        'archivo': archivo_principal,
        'archivo_url': archivo_url,
        'documento_id': documento_id,
        'comentarios': comentarios_data,
        'proyectos_relacionados': publicaciones_relacionadas_data,
        'proyectos': proyectos_relacionados_data,
        'tipo_publicacion': dict(Publicacion.TIPO_PUBLICACION_CHOICES).get(publicacion.tipo_publicacion, publicacion.tipo_publicacion),
        'doi': publicacion.doi,
        'issn': publicacion.issn,
        'isbn': publicacion.isbn,
        'url_externa': publicacion.url_externa,
    }
    
    return render(request, 'Principal/tema2/detail.html', context)


def descargar_documento(request, documento_id):
    """
    Vista para descargar un documento y registrar la descarga
    Permite descarga si el documento está asociado a una publicación accesible
    """
    documento = get_object_or_404(
        Documento.objects.select_related('proyecto'),
        id=documento_id
    )
    
    # Verificar acceso: el documento debe estar en una publicación accesible
    tiene_acceso = False
    
    # Si tiene proyecto, verificar si está en una publicación accesible
    if documento.proyecto:
        # Verificar si el proyecto está en alguna publicación
        publicaciones = documento.proyecto.publicaciones.all()
        for publicacion in publicaciones:
            # Si la publicación es pública y publicada, permitir acceso
            if publicacion.estado == 'publicada' and publicacion.visibilidad == 'publico':
                tiene_acceso = True
                break
            # Si el usuario es el editor o superusuario, permitir acceso
            elif request.user.is_authenticated and (
                request.user.is_superuser or 
                (publicacion.editor and publicacion.editor.id == request.user.id)
            ):
                tiene_acceso = True
                break
    
    # Si no tiene acceso por publicación, verificar visibilidad tradicional
    if not tiene_acceso:
        if documento.visibilidad == 'publico':
            # Si el documento es público, verificar proyecto
            if documento.proyecto:
                if documento.proyecto.estado == 'publicado' and documento.proyecto.visibilidad == 'publico':
                    tiene_acceso = True
            else:
                tiene_acceso = True
        # Si el usuario es el creador o superusuario, permitir acceso
        elif request.user.is_authenticated and (
            request.user.is_superuser or 
            (documento.creador and documento.creador.id == request.user.id)
        ):
            tiene_acceso = True
    
    if not tiene_acceso:
        raise Http404("Documento no disponible")
    
    # Obtener la versión actual
    version_actual = documento.versiones.filter(es_version_actual=True).first()
    if not version_actual:
        raise Http404("Documento sin versión disponible")
    
    # Obtener el archivo principal
    archivo_principal = version_actual.archivos.filter(es_archivo_principal=True).first()
    if not archivo_principal:
        archivo_principal = version_actual.archivos.first()
    
    if not archivo_principal or not archivo_principal.archivo:
        raise Http404("Archivo no disponible")
    
    # Registrar descarga
    ip_address = get_client_ip(request)
    DescargaArchivo.objects.create(
        archivo=archivo_principal,
        usuario=request.user if request.user.is_authenticated else None,
        ip_address=ip_address
    )
    
    # Registrar visita de tipo descarga
    VisitaDocumento.objects.create(
        documento=documento,
        usuario=request.user if request.user.is_authenticated else None,
        ip_address=ip_address,
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
        tipo_acceso='descarga',
        referer=request.META.get('HTTP_REFERER', '')[:1000]
    )
    
    # Servir el archivo
    file_path = archivo_principal.archivo.path
    if os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{archivo_principal.nombre_original}"'
            return response
    else:
        raise Http404("Archivo no encontrado en el servidor")


def comentarios_por_documento(request, documento_id):
    """
    Obtiene los comentarios públicos de un documento
    """
    try:
        documento = get_object_or_404(Documento, id=documento_id)
        
        from interaccion.models import Comentario
        comentarios = Comentario.objects.filter(
            documento=documento,
            es_publico=True
        ).select_related('usuario').order_by('-fecha_creacion')
        
        comentarios_data = []
        for comentario in comentarios:
            comentarios_data.append({
                'id': comentario.id,
                'usuario_nombre': comentario.usuario.get_full_name() or comentario.usuario.username,
                'contenido': comentario.contenido,
                'fecha_creacion': comentario.fecha_creacion.isoformat() if comentario.fecha_creacion else None,
                'fecha_creacion_str': comentario.fecha_creacion.strftime('%d de %B, %Y') if comentario.fecha_creacion else '',
            })
        
        return JsonResponse({
            'success': True,
            'data': comentarios_data,
            'total': len(comentarios_data)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def comentario_publico_create(request):
    """
    Crea un comentario público (puede ser anónimo o autenticado)
    """
    try:
        data = json.loads(request.body)
        
        documento_id = data.get('documento_id')
        if not documento_id:
            return JsonResponse({
                'success': False,
                'error': 'El documento es obligatorio'
            }, status=400)
        
        documento = get_object_or_404(Documento, id=documento_id)
        
        contenido = data.get('contenido', '').strip()
        if not contenido:
            return JsonResponse({
                'success': False,
                'error': 'El contenido es obligatorio'
            }, status=400)
        
        # Si el usuario está autenticado, usar su cuenta
        # Si no, crear un usuario temporal o permitir comentario anónimo
        from interaccion.models import Comentario
        from django.contrib.auth.models import User
        
        if request.user.is_authenticated:
            usuario = request.user
        else:
            # Para comentarios anónimos, usar un usuario genérico o crear uno temporal
            nombre_anonimo = data.get('nombre_autor', 'Anónimo').strip()
            if not nombre_anonimo:
                nombre_anonimo = 'Anónimo'
            
            # Intentar obtener o crear un usuario genérico para comentarios anónimos
            try:
                usuario = User.objects.get(username='anonimo_comentarios')
            except User.DoesNotExist:
                # Crear usuario genérico si no existe
                usuario = User.objects.create_user(
                    username='anonimo_comentarios',
                    email='anonimo@example.com',
                    first_name='Usuario',
                    last_name='Anónimo'
                )
        
        comentario = Comentario(
            documento=documento,
            usuario=usuario,
            contenido=contenido,
            es_publico=True,
            es_moderado=False
        )
        
        comentario.full_clean()
        comentario.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Comentario creado exitosamente',
            'data': {
                'id': comentario.id,
                'usuario_nombre': usuario.get_full_name() or usuario.username,
                'contenido': comentario.contenido,
                'fecha_creacion': comentario.fecha_creacion.isoformat() if comentario.fecha_creacion else None,
                'fecha_creacion_str': comentario.fecha_creacion.strftime('%d de %B, %Y') if comentario.fecha_creacion else '',
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def autor_perfil(request, user_id):
    """
    Vista de perfil de autor con sus publicaciones
    """
    autor = get_object_or_404(User, id=user_id)
    
    # Obtener publicaciones públicas donde participa el autor
    publicaciones = get_publicaciones_publicas().filter(
        proyectos__autores__usuario=autor
    ).distinct().order_by('-fecha_publicacion', '-fecha_creacion')
    
    # Paginación
    paginator = Paginator(publicaciones, 12)
    page = request.GET.get('page', 1)
    publicaciones_paginadas = paginator.get_page(page)
    
    # Preparar datos
    publicaciones_data = []
    for publicacion in publicaciones_paginadas:
        primer_proyecto = publicacion.proyectos.first()
        titulo_display = primer_proyecto.titulo if primer_proyecto else "Publicación sin título"
        resumen_display = primer_proyecto.resumen if primer_proyecto else (publicacion.descripcion or '')

        editor_nombre = publicacion.editor.get_full_name() if publicacion.editor and publicacion.editor.get_full_name() else (publicacion.editor.username if publicacion.editor else 'Sin editor')
        autores_list = get_publicacion_autores(publicacion)
        publicaciones_data.append({
            'id': publicacion.id,
            'titulo': titulo_display,
            'slug': publicacion.slug,
            'resumen': resumen_display,
            'url': f'/publicacion/{publicacion.slug}/',
            'fecha_publicacion': publicacion.fecha_publicacion,
            'fecha_publicacion_str': publicacion.fecha_publicacion.strftime('%d/%m/%Y') if publicacion.fecha_publicacion else None,
            'tipo_proyecto': dict(Publicacion.TIPO_PUBLICACION_CHOICES).get(publicacion.tipo_publicacion, publicacion.tipo_publicacion),
            'autor': ', '.join(autores_list) if autores_list else 'Sin autores',
            'autores': autores_list,
            'editor': editor_nombre,
        })
    
    query_params = request.GET.copy()
    query_params.pop('page', None)
    query_string = query_params.urlencode()

    context = {
        'autor': autor, # Pasar el objeto autor al template
        'proyectos': publicaciones_data,
        'page_obj': publicaciones_paginadas,
        'total_resultados': paginator.count,
        'query_string': query_string,
        'titulo_pagina': f"Publicaciones de {autor.get_full_name() or autor.username}",
        'sin_resultados_mensaje': 'Este autor aún no tiene publicaciones públicas registradas.',
        'is_paginated': publicaciones_paginadas.has_other_pages(),
    }
    
    return render(request, 'Principal/tema2/autor_perfil.html', context)


def categoria_proyectos(request, slug):
    """
    Vista de publicaciones por categoría
    """
    categoria = get_object_or_404(Categoria, slug=slug)
    
    # Obtener publicaciones públicas de la categoría
    publicaciones = get_publicaciones_publicas().filter(
        categorias=categoria
    ).distinct().order_by('-fecha_publicacion', '-fecha_creacion')
    
    # Paginación
    paginator = Paginator(publicaciones, 12)
    page = request.GET.get('page', 1)
    publicaciones_paginadas = paginator.get_page(page)
    
    # Preparar datos
    publicaciones_data = []
    for publicacion in publicaciones_paginadas:
        primer_proyecto = publicacion.proyectos.first()
        titulo_display = primer_proyecto.titulo if primer_proyecto else "Publicación sin título"
        resumen_display = primer_proyecto.resumen if primer_proyecto else (publicacion.descripcion or '')

        editor_nombre = publicacion.editor.get_full_name() if publicacion.editor and publicacion.editor.get_full_name() else (publicacion.editor.username if publicacion.editor else 'Sin editor')
        autores_list = get_publicacion_autores(publicacion)
        publicaciones_data.append({
            'id': publicacion.id,
            'titulo': titulo_display,
            'slug': publicacion.slug,
            'resumen': resumen_display,
            'url': f'/publicacion/{publicacion.slug}/',
            'fecha_publicacion': publicacion.fecha_publicacion,
            'fecha_publicacion_str': publicacion.fecha_publicacion.strftime('%d/%m/%Y') if publicacion.fecha_publicacion else None,
            'tipo_proyecto': dict(Publicacion.TIPO_PUBLICACION_CHOICES).get(publicacion.tipo_publicacion, publicacion.tipo_publicacion),
            'autor': ', '.join(autores_list) if autores_list else 'Sin autores',
            'autores': autores_list,
            'editor': editor_nombre,
        })
    
    tipos_publicacion, categorias, autores = get_filter_options()
    query_params = request.GET.copy()
    query_params.pop('page', None)
    query_string = query_params.urlencode()

    context = {
        'proyectos': publicaciones_data,  # Mantener para compatibilidad
        'page_obj': publicaciones_paginadas,
        'total_resultados': paginator.count,
        'query': query_params.get('q', ''),
        'selected_tipo': query_params.get('tipo', ''),
        'selected_categoria': str(categoria.id),
        'selected_autor': query_params.get('autor', ''),
        'fecha_inicio': query_params.get('fecha_inicio', ''),
        'fecha_fin': query_params.get('fecha_fin', ''),
        'tipos_proyecto': tipos_publicacion,  # Mantener para compatibilidad
        'categorias': categorias,
        'autores': autores,  # Mantener para compatibilidad
        'query_string': query_string,
        'titulo_pagina': f"Publicaciones en {categoria.nombre}",
        'sin_resultados_mensaje': 'No hay publicaciones públicas registradas en esta categoría.',
        'is_paginated': publicaciones_paginadas.has_other_pages(),
    }
    
    return render(request, 'Principal/tema2/search.html', context)


def obtener_opciones_filtros(request):
    """
    Vista AJAX para obtener opciones de filtros (rangos de fechas, etc.) para Publicaciones
    """
    # Obtener años únicos de publicaciones públicas
    años = get_publicaciones_publicas().filter(
        fecha_publicacion__isnull=False
    ).values_list('fecha_publicacion__year', flat=True).distinct().order_by('-fecha_publicacion__year')
    
    # Crear rangos de fechas
    rangos_fechas = []
    años_list = sorted(set(años), reverse=True)
    
    # Agregar rangos por año
    for año in años_list[:10]:  # Últimos 10 años
        rangos_fechas.append({
            'valor': str(año),
            'texto': str(año)
        })
    
    # Agregar rangos por décadas si hay muchos años
    if len(años_list) > 10:
        décadas = {}
        for año in años_list:
            década = (año // 10) * 10
            if década not in décadas:
                décadas[década] = década + 9
                rangos_fechas.append({
                    'valor': f'{década}-{década + 9}',
                    'texto': f'{década}-{década + 9}'
                })
    
    return JsonResponse({
        'success': True,
        'rangos_fechas': rangos_fechas
    })


def obtener_tipos_proyecto(request):
    """
    Vista AJAX para obtener tipos de publicación para filtros
    """
    # Obtener tipos de publicación únicos de publicaciones públicas
    tipos_publicacion = get_publicaciones_publicas().values_list('tipo_publicacion', flat=True).distinct()
    
    # Crear lista de opciones de tipo de publicación
    TIPO_PUBLICACION_CHOICES = dict(Publicacion.TIPO_PUBLICACION_CHOICES)
    tipos_data = [
        {'id': tipo, 'nombre': TIPO_PUBLICACION_CHOICES.get(tipo, tipo), 'slug': tipo}
        for tipo in tipos_publicacion
        if tipo in TIPO_PUBLICACION_CHOICES
    ]
    # Ordenar por nombre
    tipos_data.sort(key=lambda x: x['nombre'])
    
    return JsonResponse({
        'success': True,
        'tipos_proyecto': tipos_data  # Mantener nombre para compatibilidad
    })


def obtener_autores(request):
    """
    Vista AJAX para obtener autores para filtros
    """
    query = request.GET.get('q', '').strip()
    
    autores = User.objects.filter(
        autoria_proyectos__proyecto__publicaciones__estado='publicada',
        autoria_proyectos__proyecto__publicaciones__visibilidad='publico'
    ).distinct()
    
    if query:
        autores = autores.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(username__icontains=query) |
            Q(email__icontains=query)
        )
    
    autores = autores.order_by('first_name', 'last_name', 'username')[:50]
    
    autores_data = []
    for autor in autores:
        autores_data.append({
            'id': autor.id,
            'nombre': autor.get_full_name() or autor.username,
            'username': autor.username,
        })
    
    return JsonResponse({
        'success': True,
        'autores': autores_data  # Mantener nombre para compatibilidad
    })


def obtener_categorias(request):
    """
    Vista AJAX para obtener categorías para filtros de Publicaciones
    """
    categorias = Categoria.objects.filter(
        publicaciones__estado='publicada',
        publicaciones__visibilidad='publico'
    ).distinct().order_by('nombre')
    
    categorias_data = []
    for categoria in categorias:
        categorias_data.append({
            'id': categoria.id,
            'nombre': categoria.nombre,
            'slug': categoria.slug,
        })
    
    return JsonResponse({
        'success': True,
        'categorias': categorias_data
    })
