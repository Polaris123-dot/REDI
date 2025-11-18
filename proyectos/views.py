from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.forms.models import model_to_dict
from django.utils.text import slugify
import json
from .models import TipoProyecto, CampoTipoProyecto, Proyecto, ValorCampoProyecto, ProyectoAutor
from django.contrib.auth.models import User
from django.db import transaction


@login_required
@ensure_csrf_cookie
@require_http_methods(["GET"])
def index(request):
    """Vista principal de proyectos"""
    # Verificar permisos
    if not (request.user.has_perm('proyectos.view_proyecto') or 
            request.user.has_perm('proyectos.view_tipoproyecto') or 
            request.user.is_superuser):
        messages.warning(request, 'No tienes permisos para acceder a proyectos.')
        return redirect('usuarios:panel')
    return render(request, 'proyectos/index.html')


# ============================================================================
# VISTAS PARA TIPOS DE PROYECTO
# ============================================================================

@login_required
@require_http_methods(["GET"])
def tipos_proyecto_list(request):
    """Lista todos los tipos de proyecto en formato JSON"""
    tipos = TipoProyecto.objects.all()
    tipos_data = []
    
    for tipo in tipos:
        tipo_dict = {
            'id': tipo.id,
            'nombre': tipo.nombre,
            'slug': tipo.slug,
            'descripcion': tipo.descripcion or '',
            'icono': tipo.icono or '',
            'color': tipo.color or '',
            'plantilla_vista': tipo.plantilla_vista or '',
            'es_activo': tipo.es_activo,
            'orden': tipo.orden,
            'fecha_creacion': tipo.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S') if tipo.fecha_creacion else None,
        }
        tipos_data.append(tipo_dict)
    
    return JsonResponse({
        'success': True,
        'data': tipos_data
    })


@login_required
@require_http_methods(["GET"])
def tipos_proyecto_for_select(request):
    """Lista tipos de proyecto para usar en selects"""
    tipos = TipoProyecto.objects.filter(es_activo=True).order_by('orden', 'nombre')
    tipos_data = [{'id': t.id, 'nombre': t.nombre} for t in tipos]
    
    return JsonResponse({
        'success': True,
        'data': tipos_data
    })


@login_required
@require_http_methods(["POST"])
@transaction.atomic
def tipo_proyecto_create(request):
    """Crea un nuevo tipo de proyecto"""
    try:
        data = json.loads(request.body)
        
        nombre = data.get('nombre', '').strip()
        if not nombre:
            return JsonResponse({'success': False, 'error': 'El nombre es obligatorio'}, status=400)
        
        slug = slugify(nombre)
        if not slug:
            return JsonResponse({'success': False, 'error': 'No se pudo generar un slug válido'}, status=400)
        
        if TipoProyecto.objects.filter(slug=slug).exists():
            return JsonResponse({'success': False, 'error': 'Ya existe un tipo de proyecto con este nombre'}, status=400)
        
        tipo = TipoProyecto.objects.create(
            nombre=nombre,
            slug=slug,
            descripcion=data.get('descripcion', '').strip() or None,
            icono=data.get('icono', '').strip() or None,
            color=data.get('color', '').strip() or None,
            plantilla_vista=data.get('plantilla_vista', '').strip() or None,
            es_activo=data.get('es_activo', True),
            orden=data.get('orden', 0)
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Tipo de proyecto creado exitosamente',
            'data': {
                'id': tipo.id,
                'nombre': tipo.nombre,
                'slug': tipo.slug,
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def tipo_proyecto_detail(request, tipo_proyecto_id):
    """Obtiene los detalles de un tipo de proyecto"""
    try:
        tipo = get_object_or_404(TipoProyecto, id=tipo_proyecto_id)
        return JsonResponse({
            'success': True,
            'data': {
                'id': tipo.id,
                'nombre': tipo.nombre,
                'slug': tipo.slug,
                'descripcion': tipo.descripcion or '',
                'icono': tipo.icono or '',
                'color': tipo.color or '',
                'plantilla_vista': tipo.plantilla_vista or '',
                'es_activo': tipo.es_activo,
                'orden': tipo.orden,
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST", "PUT"])
@transaction.atomic
def tipo_proyecto_update(request, tipo_proyecto_id):
    """Actualiza un tipo de proyecto"""
    try:
        tipo = get_object_or_404(TipoProyecto, id=tipo_proyecto_id)
        data = json.loads(request.body)
        
        nombre = data.get('nombre', '').strip()
        if not nombre:
            return JsonResponse({'success': False, 'error': 'El nombre es obligatorio'}, status=400)
        
        nuevo_slug = slugify(nombre)
        if nuevo_slug != tipo.slug:
            if TipoProyecto.objects.filter(slug=nuevo_slug).exclude(id=tipo_proyecto_id).exists():
                return JsonResponse({'success': False, 'error': 'Ya existe un tipo de proyecto con este nombre'}, status=400)
            tipo.slug = nuevo_slug
        
        tipo.nombre = nombre
        tipo.descripcion = data.get('descripcion', '').strip() or None
        tipo.icono = data.get('icono', '').strip() or None
        tipo.color = data.get('color', '').strip() or None
        tipo.plantilla_vista = data.get('plantilla_vista', '').strip() or None
        tipo.es_activo = data.get('es_activo', tipo.es_activo)
        tipo.orden = data.get('orden', tipo.orden)
        tipo.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Tipo de proyecto actualizado exitosamente',
            'data': {
                'id': tipo.id,
                'nombre': tipo.nombre,
                'slug': tipo.slug,
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST", "DELETE"])
@transaction.atomic
def tipo_proyecto_delete(request, tipo_proyecto_id):
    """Elimina un tipo de proyecto"""
    try:
        tipo = get_object_or_404(TipoProyecto, id=tipo_proyecto_id)
        
        if request.method == 'POST':
            data = json.loads(request.body) if request.body else {}
            if data.get('_method') != 'DELETE':
                return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
        
        if tipo.proyectos.exists():
            return JsonResponse({
                'success': False,
                'error': 'No se puede eliminar este tipo de proyecto porque tiene proyectos asociados'
            }, status=400)
        
        tipo_nombre = tipo.nombre
        tipo.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Tipo de proyecto "{tipo_nombre}" eliminado exitosamente'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ============================================================================
# VISTAS PARA CAMPOS DE TIPO DE PROYECTO
# ============================================================================

@login_required
@require_http_methods(["GET"])
def campos_tipo_proyecto_list(request):
    """Lista todos los campos de tipo de proyecto"""
    campos = CampoTipoProyecto.objects.select_related('tipo_proyecto').all().order_by('tipo_proyecto__nombre', 'orden', 'nombre')
    campos_data = []
    
    for campo in campos:
        campo_dict = {
            'id': campo.id,
            'tipo_proyecto_id': campo.tipo_proyecto.id,
            'tipo_proyecto_nombre': campo.tipo_proyecto.nombre,
            'nombre': campo.nombre,
            'slug': campo.slug,
            'tipo_dato': campo.tipo_dato,
            'es_obligatorio': campo.es_obligatorio,
            'es_repetible': campo.es_repetible,
            'orden': campo.orden,
            'descripcion': campo.descripcion or '',
            'valores_posibles': campo.valores_posibles or [],
        }
        campos_data.append(campo_dict)
    
    return JsonResponse({
        'success': True,
        'data': campos_data
    })


@login_required
@require_http_methods(["GET"])
def campos_por_tipo_proyecto(request, tipo_proyecto_id):
    """Lista los campos de un tipo de proyecto específico"""
    try:
        tipo_proyecto = get_object_or_404(TipoProyecto, id=tipo_proyecto_id)
        campos = CampoTipoProyecto.objects.filter(tipo_proyecto=tipo_proyecto).order_by('orden', 'nombre')
        campos_data = []
        
        for campo in campos:
            campo_dict = {
                'id': campo.id,
                'nombre': campo.nombre,
                'slug': campo.slug,
                'tipo_dato': campo.tipo_dato,
                'es_obligatorio': campo.es_obligatorio,
                'es_repetible': campo.es_repetible,
                'orden': campo.orden,
                'descripcion': campo.descripcion or '',
                'valores_posibles': campo.valores_posibles or [],
            }
            campos_data.append(campo_dict)
        
        return JsonResponse({
            'success': True,
            'data': campos_data
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
@transaction.atomic
def campo_tipo_proyecto_create(request):
    """Crea un nuevo campo de tipo de proyecto"""
    try:
        data = json.loads(request.body)
        
        tipo_proyecto_id = data.get('tipo_proyecto_id')
        if not tipo_proyecto_id:
            return JsonResponse({'success': False, 'error': 'El tipo de proyecto es obligatorio'}, status=400)
        
        tipo_proyecto = get_object_or_404(TipoProyecto, id=tipo_proyecto_id)
        
        nombre = data.get('nombre', '').strip()
        if not nombre:
            return JsonResponse({'success': False, 'error': 'El nombre es obligatorio'}, status=400)
        
        slug = slugify(nombre)
        if CampoTipoProyecto.objects.filter(tipo_proyecto=tipo_proyecto, slug=slug).exists():
            return JsonResponse({'success': False, 'error': 'Ya existe un campo con este nombre en este tipo de proyecto'}, status=400)
        
        campo = CampoTipoProyecto.objects.create(
            tipo_proyecto=tipo_proyecto,
            nombre=nombre,
            slug=slug,
            tipo_dato=data.get('tipo_dato', 'texto'),
            es_obligatorio=data.get('es_obligatorio', False),
            es_repetible=data.get('es_repetible', False),
            orden=data.get('orden', 0),
            descripcion=data.get('descripcion', '').strip() or None,
            valores_posibles=data.get('valores_posibles', []) if data.get('valores_posibles') else None,
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Campo creado exitosamente',
            'data': {
                'id': campo.id,
                'nombre': campo.nombre,
                'slug': campo.slug,
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def campo_tipo_proyecto_detail(request, campo_id):
    """Obtiene los detalles de un campo de tipo de proyecto"""
    try:
        campo = get_object_or_404(CampoTipoProyecto, id=campo_id)
        return JsonResponse({
            'success': True,
            'data': {
                'id': campo.id,
                'tipo_proyecto_id': campo.tipo_proyecto.id,
                'tipo_proyecto_nombre': campo.tipo_proyecto.nombre,
                'nombre': campo.nombre,
                'slug': campo.slug,
                'tipo_dato': campo.tipo_dato,
                'es_obligatorio': campo.es_obligatorio,
                'es_repetible': campo.es_repetible,
                'orden': campo.orden,
                'descripcion': campo.descripcion or '',
                'valores_posibles': campo.valores_posibles or [],
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST", "PUT"])
@transaction.atomic
def campo_tipo_proyecto_update(request, campo_id):
    """Actualiza un campo de tipo de proyecto"""
    try:
        campo = get_object_or_404(CampoTipoProyecto, id=campo_id)
        data = json.loads(request.body)
        
        nombre = data.get('nombre', '').strip()
        if not nombre:
            return JsonResponse({'success': False, 'error': 'El nombre es obligatorio'}, status=400)
        
        nuevo_slug = slugify(nombre)
        if nuevo_slug != campo.slug:
            if CampoTipoProyecto.objects.filter(tipo_proyecto=campo.tipo_proyecto, slug=nuevo_slug).exclude(id=campo_id).exists():
                return JsonResponse({'success': False, 'error': 'Ya existe un campo con este nombre en este tipo de proyecto'}, status=400)
            campo.slug = nuevo_slug
        
        campo.nombre = nombre
        campo.tipo_dato = data.get('tipo_dato', campo.tipo_dato)
        campo.es_obligatorio = data.get('es_obligatorio', campo.es_obligatorio)
        campo.es_repetible = data.get('es_repetible', campo.es_repetible)
        campo.orden = data.get('orden', campo.orden)
        campo.descripcion = data.get('descripcion', '').strip() or None
        campo.valores_posibles = data.get('valores_posibles', []) if data.get('valores_posibles') else None
        campo.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Campo actualizado exitosamente',
            'data': {
                'id': campo.id,
                'nombre': campo.nombre,
                'slug': campo.slug,
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST", "DELETE"])
@transaction.atomic
def campo_tipo_proyecto_delete(request, campo_id):
    """Elimina un campo de tipo de proyecto"""
    try:
        campo = get_object_or_404(CampoTipoProyecto, id=campo_id)
        
        if request.method == 'POST':
            data = json.loads(request.body) if request.body else {}
            if data.get('_method') != 'DELETE':
                return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
        
        campo_nombre = campo.nombre
        campo.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Campo "{campo_nombre}" eliminado exitosamente'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ============================================================================
# VISTAS PARA PROYECTOS
# ============================================================================

@login_required
@require_http_methods(["GET"])
def proyectos_list(request):
    """Lista todos los proyectos en formato JSON"""
    proyectos = Proyecto.objects.select_related('tipo_proyecto', 'creador', 'documento').prefetch_related('autores__usuario', 'categorias', 'etiquetas').all().order_by('-fecha_creacion')
    proyectos_data = []
    
    for proyecto in proyectos:
        autores = []
        for autor in proyecto.autores.all():
            autores.append({
                'id': autor.id,
                'usuario_id': autor.usuario.id,
                'usuario_nombre': autor.usuario.get_full_name() or autor.usuario.username,
                'afiliacion': autor.afiliacion or '',
                'orden_autor': autor.orden_autor,
                'es_correspondiente': autor.es_correspondiente,
                'es_autor_principal': autor.es_autor_principal,
                'orcid_id': autor.orcid_id or ''
            })
        
        proyecto_dict = {
            'id': proyecto.id,
            'titulo': proyecto.titulo,
            'slug': proyecto.slug,
            'tipo_proyecto_id': proyecto.tipo_proyecto.id,
            'tipo_proyecto_nombre': proyecto.tipo_proyecto.nombre,
            'creador_id': proyecto.creador.id,
            'creador_nombre': proyecto.creador.get_full_name() or proyecto.creador.username,
            'resumen': proyecto.resumen or '',
            'descripcion': proyecto.descripcion or '',
            'estado': proyecto.estado,
            'estado_display': proyecto.get_estado_display(),
            'visibilidad': proyecto.visibilidad,
            'visibilidad_display': proyecto.get_visibilidad_display(),
            'fecha_creacion': proyecto.fecha_creacion.isoformat() if proyecto.fecha_creacion else None,
            'fecha_actualizacion': proyecto.fecha_actualizacion.isoformat() if proyecto.fecha_actualizacion else None,
            'fecha_publicacion': proyecto.fecha_publicacion.isoformat() if proyecto.fecha_publicacion else None,
            'version': proyecto.version,
            'categorias_count': proyecto.categorias.count(),
            'etiquetas_count': proyecto.etiquetas.count(),
            'autores_count': proyecto.autores.count(),
            'autores': autores,
            'documento_id': None,
        }
        try:
            proyecto_dict['documento_id'] = proyecto.documento.id
        except Exception:
            # RelatedObjectDoesNotExist o cualquier otra excepción
            proyecto_dict['documento_id'] = None
        proyectos_data.append(proyecto_dict)
    
    return JsonResponse({
        'success': True,
        'data': proyectos_data,
        'total': len(proyectos_data)
    })


@login_required
@require_http_methods(["GET"])
def proyectos_por_tipo(request, tipo_proyecto_id):
    """Lista proyectos de un tipo específico"""
    try:
        tipo_proyecto = get_object_or_404(TipoProyecto, id=tipo_proyecto_id)
        proyectos = Proyecto.objects.filter(tipo_proyecto=tipo_proyecto).order_by('-fecha_creacion')
        proyectos_data = [{'id': p.id, 'titulo': p.titulo, 'slug': p.slug} for p in proyectos]
        
        return JsonResponse({
            'success': True,
            'data': proyectos_data
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def proyecto_detail(request, proyecto_id):
    """Obtiene los detalles de un proyecto"""
    try:
        proyecto = get_object_or_404(Proyecto, id=proyecto_id)
        
        autores = []
        for autor in proyecto.autores.all():
            autores.append({
                'id': autor.id,
                'usuario_id': autor.usuario.id,
                'usuario_nombre': autor.usuario.get_full_name() or autor.usuario.username,
                'afiliacion': autor.afiliacion or '',
                'orden_autor': autor.orden_autor,
                'es_correspondiente': autor.es_correspondiente,
                'es_autor_principal': autor.es_autor_principal,
                'orcid_id': autor.orcid_id or ''
            })
        
        valores_campos = {}
        for valor in proyecto.valores_campos.select_related('campo_tipo_proyecto').all():
            campo_slug = valor.campo_tipo_proyecto.slug
            if valor.campo_tipo_proyecto.es_repetible:
                if campo_slug not in valores_campos:
                    valores_campos[campo_slug] = []
                valores_campos[campo_slug].append(valor.get_valor())
            else:
                valores_campos[campo_slug] = valor.get_valor()
        
        proyecto_dict = {
            'id': proyecto.id,
            'titulo': proyecto.titulo,
            'slug': proyecto.slug,
            'tipo_proyecto_id': proyecto.tipo_proyecto.id,
            'tipo_proyecto_nombre': proyecto.tipo_proyecto.nombre,
            'creador_id': proyecto.creador.id,
            'creador_nombre': proyecto.creador.get_full_name() or proyecto.creador.username,
            'resumen': proyecto.resumen or '',
            'descripcion': proyecto.descripcion or '',
            'estado': proyecto.estado,
            'estado_display': proyecto.get_estado_display(),
            'visibilidad': proyecto.visibilidad,
            'visibilidad_display': proyecto.get_visibilidad_display(),
            'fecha_creacion': proyecto.fecha_creacion.isoformat() if proyecto.fecha_creacion else None,
            'fecha_actualizacion': proyecto.fecha_actualizacion.isoformat() if proyecto.fecha_actualizacion else None,
            'fecha_publicacion': proyecto.fecha_publicacion.isoformat() if proyecto.fecha_publicacion else None,
            'version': proyecto.version,
            'categorias_count': proyecto.categorias.count(),
            'etiquetas_count': proyecto.etiquetas.count(),
            'autores_count': proyecto.autores.count(),
            'autores': autores,
            'valores_campos': valores_campos,
            'documento_id': None,
        }
        try:
            proyecto_dict['documento_id'] = proyecto.documento.id
        except Exception:
            # RelatedObjectDoesNotExist o cualquier otra excepción
            proyecto_dict['documento_id'] = None
        
        return JsonResponse({
            'success': True,
            'data': proyecto_dict
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener proyecto: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
@transaction.atomic
def proyecto_create(request):
    """Crea un nuevo proyecto con campos dinámicos y subida de archivo."""
    try:
        # Los datos ahora vienen de request.POST y request.FILES
        data = request.POST
        
        # Validar campos requeridos
        tipo_proyecto_id = data.get('tipo_proyecto_id')
        if not tipo_proyecto_id:
            return JsonResponse({'success': False, 'error': 'El tipo de proyecto es obligatorio'}, status=400)
        
        tipo_proyecto = get_object_or_404(TipoProyecto, id=tipo_proyecto_id)
        
        # Validar documento (ahora es requerido)
        documento_id = data.get('documento_id')
        if not documento_id:
            return JsonResponse({'success': False, 'error': 'El documento es obligatorio'}, status=400)
        
        try:
            from repositorio.models import Documento
            documento = Documento.objects.get(id=documento_id)
            # Verificar que el documento no tenga ya un proyecto asociado
            if documento.proyecto:
                return JsonResponse({
                    'success': False,
                    'error': 'Este documento ya está asociado a otro proyecto'
                }, status=400)
        except Documento.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'El documento no existe'}, status=400)
        
        # Obtener título y resumen del documento
        titulo = documento.get_titulo() if hasattr(documento, 'get_titulo') else (documento.titulo or f'Proyecto #{Documento.objects.count() + 1}')
        resumen = documento.get_resumen() if hasattr(documento, 'get_resumen') else (documento.resumen or None)
        
        # Generar slug
        nuevo_slug = slugify(titulo)
        if not nuevo_slug:
            return JsonResponse({'success': False, 'error': 'El título del documento no puede generar un slug válido'}, status=400)
        
        contador = 1
        slug_base = nuevo_slug
        while Proyecto.objects.filter(slug=nuevo_slug).exists():
            nuevo_slug = f"{slug_base}-{contador}"
            contador += 1
        
        # Crear el proyecto
        proyecto = Proyecto(
            titulo=titulo,
            slug=nuevo_slug,
            tipo_proyecto=tipo_proyecto,
            creador=request.user,
            resumen=resumen,
            descripcion=data.get('descripcion', '').strip() or None,
            estado=data.get('estado', 'borrador'),
            visibilidad=data.get('visibilidad', 'publico'),
            version=1
        )
        proyecto.full_clean()
        proyecto.save()
        
        # Asociar el documento al proyecto (requerido)
        documento.proyecto = proyecto
        documento.save()

        # Procesar campos dinámicos (enviados como JSON en un campo de texto)
        campos_dinamicos_str = data.get('campos_dinamicos', '{}')
        campos_dinamicos = json.loads(campos_dinamicos_str)
        for campo_slug, valores in campos_dinamicos.items():
            try:
                campo_tipo = CampoTipoProyecto.objects.get(tipo_proyecto=tipo_proyecto, slug=campo_slug)
                if campo_tipo.es_repetible and isinstance(valores, list):
                    for orden, valor in enumerate(valores):
                        ValorCampoProyecto.objects.create(proyecto=proyecto, campo_tipo_proyecto=campo_tipo, orden=orden).set_valor(valor)
                else:
                    valor = valores[0] if isinstance(valores, list) and valores else valores
                    if valor is not None and valor != '':
                        ValorCampoProyecto.objects.create(proyecto=proyecto, campo_tipo_proyecto=campo_tipo, orden=0).set_valor(valor)
            except CampoTipoProyecto.DoesNotExist:
                continue
        
        # Procesar autores (enviados como JSON en un campo de texto)
        autores_str = data.get('autores', '[]')
        autores_data = json.loads(autores_str)
        for idx, autor_data in enumerate(autores_data):
            usuario_id = autor_data.get('usuario_id')
            if usuario_id:
                try:
                    usuario = User.objects.get(id=usuario_id)
                    ProyectoAutor.objects.create(
                        proyecto=proyecto,
                        usuario=usuario,
                        afiliacion=autor_data.get('afiliacion', '').strip() or None,
                        orden_autor=autor_data.get('orden_autor', idx + 1),
                        es_correspondiente=autor_data.get('es_correspondiente', False),
                        es_autor_principal=autor_data.get('es_autor_principal', False),
                        orcid_id=autor_data.get('orcid_id', '').strip() or None
                    )
                except User.DoesNotExist:
                    continue
        
        return JsonResponse({
            'success': True,
            'message': 'Proyecto creado exitosamente',
            'data': {
                'id': proyecto.id,
                'titulo': proyecto.titulo,
                'slug': proyecto.slug,
            }
        })
    except ValidationError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON inválido en campos dinámicos o autores'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error al crear proyecto: {str(e)}'}, status=500)


@login_required
@require_http_methods(["POST", "PUT"])
@transaction.atomic
def proyecto_update(request, proyecto_id):
    """Actualiza un proyecto existente"""
    try:
        proyecto = get_object_or_404(Proyecto, id=proyecto_id)
        
        if request.method == 'POST':
            data = request.POST
        else:
            data = json.loads(request.body)
        
        # Título y resumen vienen del documento, no se actualizan aquí
        # Si se cambia el documento, actualizar título y resumen
        nuevo_documento_id = data.get('documento_id')
        try:
            documento_actual = proyecto.documento
            documento_actual_id = str(documento_actual.id)
        except Exception:
            # RelatedObjectDoesNotExist o cualquier otra excepción
            documento_actual = None
            documento_actual_id = ''
        
        if nuevo_documento_id and str(nuevo_documento_id) != documento_actual_id:
            try:
                from repositorio.models import Documento
                nuevo_documento = Documento.objects.get(id=nuevo_documento_id)
                if nuevo_documento.proyecto and nuevo_documento.proyecto.id != proyecto.id:
                    return JsonResponse({
                        'success': False,
                        'error': 'Este documento ya está asociado a otro proyecto'
                    }, status=400)
                # Desasociar documento anterior
                if documento_actual:
                    documento_actual.proyecto = None
                    documento_actual.save()
                # Asociar nuevo documento
                nuevo_documento.proyecto = proyecto
                nuevo_documento.save()
                # Actualizar título y resumen del proyecto
                proyecto.titulo = nuevo_documento.get_titulo() if hasattr(nuevo_documento, 'get_titulo') else (nuevo_documento.titulo or proyecto.titulo)
                proyecto.resumen = nuevo_documento.get_resumen() if hasattr(nuevo_documento, 'get_resumen') else (nuevo_documento.resumen or proyecto.resumen)
                # Regenerar slug
                nuevo_slug = slugify(proyecto.titulo)
                if nuevo_slug and nuevo_slug != proyecto.slug:
                    slug_base = nuevo_slug
                    contador = 1
                    while Proyecto.objects.filter(slug=nuevo_slug).exclude(id=proyecto_id).exists():
                        nuevo_slug = f"{slug_base}-{contador}"
                        contador += 1
                    proyecto.slug = nuevo_slug
            except Documento.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'El documento no existe'}, status=400)
        elif documento_actual:
            # Si no se cambia el documento, actualizar título y resumen desde el documento actual
            proyecto.titulo = documento_actual.get_titulo() if hasattr(documento_actual, 'get_titulo') else (documento_actual.titulo or proyecto.titulo)
            proyecto.resumen = documento_actual.get_resumen() if hasattr(documento_actual, 'get_resumen') else (documento_actual.resumen or proyecto.resumen)
        proyecto.descripcion = data.get('descripcion', '').strip() or None
        proyecto.estado = data.get('estado', proyecto.estado)
        proyecto.visibilidad = data.get('visibilidad', proyecto.visibilidad)
        
        proyecto.full_clean()
        proyecto.save()
        
        # Actualizar valores de campos dinámicos
        campos_dinamicos = data.get('campos_dinamicos', {})
        if isinstance(campos_dinamicos, str):
            campos_dinamicos = json.loads(campos_dinamicos)
        if campos_dinamicos:
            # Eliminar valores existentes
            proyecto.valores_campos.all().delete()
            
            # Crear nuevos valores
            for campo_slug, valores in campos_dinamicos.items():
                try:
                    campo_tipo = CampoTipoProyecto.objects.get(tipo_proyecto=proyecto.tipo_proyecto, slug=campo_slug)
                    
                    if campo_tipo.es_repetible and isinstance(valores, list):
                        for orden, valor in enumerate(valores):
                            ValorCampoProyecto.objects.create(proyecto=proyecto, campo_tipo_proyecto=campo_tipo, orden=orden).set_valor(valor)
                    else:
                        valor = valores[0] if isinstance(valores, list) and valores else valores
                        if valor is not None and valor != '':
                            ValorCampoProyecto.objects.create(proyecto=proyecto, campo_tipo_proyecto=campo_tipo, orden=0).set_valor(valor)
                except CampoTipoProyecto.DoesNotExist:
                    continue
        
        # Actualizar autores
        autores_data = data.get('autores', [])
        if isinstance(autores_data, str):
            autores_data = json.loads(autores_data)
        if autores_data is not None:
            proyecto.autores.all().delete()
            for idx, autor_data in enumerate(autores_data):
                usuario_id = autor_data.get('usuario_id')
                if usuario_id:
                    try:
                        usuario = User.objects.get(id=usuario_id)
                        ProyectoAutor.objects.create(
                            proyecto=proyecto,
                            usuario=usuario,
                            afiliacion=autor_data.get('afiliacion', '').strip() or None,
                            orden_autor=autor_data.get('orden_autor', idx + 1),
                            es_correspondiente=autor_data.get('es_correspondiente', False),
                            es_autor_principal=autor_data.get('es_autor_principal', False),
                            orcid_id=autor_data.get('orcid_id', '').strip() or None
                        )
                    except User.DoesNotExist:
                        continue
        
        return JsonResponse({
            'success': True,
            'message': 'Proyecto actualizado exitosamente',
            'data': {
                'id': proyecto.id,
                'titulo': proyecto.titulo,
                'slug': proyecto.slug,
            }
        })
        
    except ValidationError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'JSON inválido'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al actualizar proyecto: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "DELETE"])
@transaction.atomic
def proyecto_delete(request, proyecto_id):
    """Elimina un proyecto"""
    try:
        proyecto = get_object_or_404(Proyecto, id=proyecto_id)
        
        if request.method == 'POST':
            data = json.loads(request.body) if request.body else {}
            if data.get('_method') != 'DELETE':
                return JsonResponse({
                    'success': False,
                    'error': 'Método no permitido'
                }, status=405)
        
        proyecto_titulo = proyecto.titulo
        proyecto.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Proyecto "{proyecto_titulo}" eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al eliminar proyecto: {str(e)}'
        }, status=500)


# ============================================================================
# VISTAS AUXILIARES
# ============================================================================

@login_required
@require_http_methods(["GET"])
def usuarios_for_select(request):
    """Lista usuarios para usar en selects"""
    usuarios = User.objects.filter(is_active=True).order_by('username')
    usuarios_data = [{'id': u.id, 'nombre': u.get_full_name() or u.username, 'username': u.username} for u in usuarios]
    
    return JsonResponse({
        'success': True,
        'data': usuarios_data
    })


# ============================================================================
# WIZARD DE ACCESO RÁPIDO
# ============================================================================

@login_required
@ensure_csrf_cookie
@require_http_methods(["GET"])
def wizard_rapido(request):
    """Wizard de acceso rápido para crear Documento -> Archivo -> Proyecto -> Publicación"""
    # Verificar permisos
    if not (request.user.has_perm('proyectos.add_proyecto') or 
            request.user.has_perm('repositorio.add_documento') or 
            request.user.is_superuser):
        messages.warning(request, 'No tienes permisos para acceder al wizard rápido.')
        return redirect('usuarios:panel')
    return render(request, 'proyectos/wizard_rapido.html')
