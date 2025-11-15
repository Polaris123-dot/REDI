from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.forms.models import model_to_dict
from django.utils.text import slugify
from django.db import transaction
from django.contrib.auth.models import User
import json
from datetime import datetime
from .models import Publicacion, PublicacionProyecto
from proyectos.models import Proyecto
from catalogacion.models import Categoria, Etiqueta


@login_required
@ensure_csrf_cookie
@require_http_methods(["GET"])
def index(request):
    """Vista principal de publicaciones"""
    # Verificar permisos
    if not (request.user.has_perm('publicaciones.view_publicacion') or 
            request.user.is_superuser):
        messages.warning(request, 'No tienes permisos para acceder a publicaciones.')
        return redirect('usuarios:panel')
    return render(request, 'publicaciones/index.html')


# ============================================================================
# VISTAS PARA PUBLICACIONES
# ============================================================================

@login_required
@require_http_methods(["GET"])
def publicaciones_list(request):
    """Lista todas las publicaciones en formato JSON"""
    publicaciones = Publicacion.objects.all().select_related('editor').prefetch_related('proyectos')
    publicaciones_data = []
    
    for pub in publicaciones:
        primer_proyecto = pub.proyectos.first()
        titulo_display = primer_proyecto.titulo if primer_proyecto else "Publicación sin título"
        descripcion_display = primer_proyecto.resumen if primer_proyecto else ""

        editor_nombre = pub.editor.get_full_name() if pub.editor.get_full_name() else pub.editor.username
        pub_dict = {
            'id': pub.id,
            'titulo': titulo_display,
            'slug': pub.slug,
            'descripcion': descripcion_display,
            'tipo_publicacion': pub.tipo_publicacion,
            'tipo_publicacion_display': pub.get_tipo_publicacion_display(),
            'editor_id': pub.editor.id,
            'editor_nombre': editor_nombre,
            'estado': pub.estado,
            'estado_display': pub.get_estado_display(),
            'fecha_creacion': pub.fecha_creacion.isoformat() if pub.fecha_creacion else None,
            'fecha_actualizacion': pub.fecha_actualizacion.isoformat() if pub.fecha_actualizacion else None,
            'fecha_publicacion': pub.fecha_publicacion.isoformat() if pub.fecha_publicacion else None,
            'issn': pub.issn or '',
            'isbn': pub.isbn or '',
            'doi': pub.doi or '',
            'url_externa': pub.url_externa or '',
            'proyectos_count': pub.proyectos.count(),
            'categorias_count': pub.categorias.count(),
            'etiquetas_count': pub.etiquetas.count(),
        }
        publicaciones_data.append(pub_dict)
    
    return JsonResponse({
        'success': True,
        'data': publicaciones_data
    })


@login_required
@require_http_methods(["GET"])
def publicacion_detail(request, publicacion_id):
    """Obtiene los detalles de una publicación en formato JSON"""
    try:
        pub = get_object_or_404(Publicacion.objects.prefetch_related('proyectos'), id=publicacion_id)
        
        # Obtener proyectos asociados con información adicional
        proyectos_data = []
        for pub_proy in pub.proyectos_relacionados.all().select_related('proyecto'):
            proyectos_data.append({
                'id': pub_proy.proyecto.id,
                'titulo': pub_proy.proyecto.titulo,
                'orden': pub_proy.orden,
                'rol_en_publicacion': pub_proy.rol_en_publicacion or '',
                'fecha_incorporacion': pub_proy.fecha_incorporacion.isoformat() if pub_proy.fecha_incorporacion else None,
            })
        
        # Obtener categorías asociadas
        categorias_data = [{'id': cat.id, 'nombre': cat.nombre} for cat in pub.categorias.all()]
        
        # Obtener etiquetas asociadas
        etiquetas_data = [{'id': etq.id, 'nombre': etq.nombre} for etq in pub.etiquetas.all()]
        
        primer_proyecto = pub.proyectos.first()
        titulo_display = primer_proyecto.titulo if primer_proyecto else "Publicación sin título"
        descripcion_display = primer_proyecto.resumen if primer_proyecto else ""

        pub_dict = {
            'id': pub.id,
            'titulo': titulo_display,
            'slug': pub.slug,
            'descripcion': descripcion_display,
            'tipo_publicacion': pub.tipo_publicacion,
            'editor_id': pub.editor.id,
            'estado': pub.estado,
            'fecha_creacion': pub.fecha_creacion.isoformat() if pub.fecha_creacion else None,
            'fecha_actualizacion': pub.fecha_actualizacion.isoformat() if pub.fecha_actualizacion else None,
            'fecha_publicacion': pub.fecha_publicacion.isoformat() if pub.fecha_publicacion else None,
            'issn': pub.issn or '',
            'isbn': pub.isbn or '',
            'doi': pub.doi or '',
            'url_externa': pub.url_externa or '',
            'metadata': pub.metadata or {},
            'proyectos': proyectos_data,
            'categorias': categorias_data,
            'etiquetas': etiquetas_data,
        }
        
        return JsonResponse({
            'success': True,
            'data': pub_dict
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
@transaction.atomic
def publicacion_create(request):
    """Crea una nueva publicación"""
    try:
        data = json.loads(request.body)
        
        # Validar que se haya enviado al menos un proyecto
        proyectos_data = data.get('proyectos', [])
        if not proyectos_data:
            return JsonResponse({
                'success': False,
                'error': 'Se debe asociar al menos un proyecto a la publicación.'
            }, status=400)

        # Obtener el primer proyecto para usar su ID en el slug
        primer_proyecto_id = proyectos_data[0].get('id') if isinstance(proyectos_data[0], dict) else proyectos_data[0]
        if not primer_proyecto_id:
            return JsonResponse({
                'success': False,
                'error': 'El primer proyecto asociado no tiene un ID válido.'
            }, status=400)
        
        # Generar slug único a partir de un timestamp y el ID del proyecto
        timestamp = int(datetime.now().timestamp())
        slug_base = f"{timestamp}-{primer_proyecto_id}"
        slug = slug_base
        
        # Verificar que el slug no exista (aunque es muy improbable)
        contador = 1
        while Publicacion.objects.filter(slug=slug).exists():
            slug = f"{slug_base}-{contador}"
            contador += 1
        
        # Validar editor
        editor_id = data.get('editor_id')
        if not editor_id:
            editor_id = request.user.id
        editor = get_object_or_404(User, id=editor_id)
        
        # Validar tipo de publicación
        tipo_publicacion = data.get('tipo_publicacion', 'repositorio')
        if tipo_publicacion not in [choice[0] for choice in Publicacion.TIPO_PUBLICACION_CHOICES]:
            tipo_publicacion = 'repositorio'
        
        # Validar estado
        estado = data.get('estado', 'borrador')
        if estado not in [choice[0] for choice in Publicacion.ESTADO_CHOICES]:
            estado = 'borrador'
        
        # Procesar fecha de publicación
        fecha_publicacion = data.get('fecha_publicacion')
        if fecha_publicacion:
            try:
                fecha_publicacion = datetime.fromisoformat(fecha_publicacion.replace('Z', '+00:00'))
            except:
                fecha_publicacion = None
        
        # Crear la publicación con título y descripción nulos
        publicacion = Publicacion(
            titulo=None,
            slug=slug,
            descripcion=None,
            tipo_publicacion=tipo_publicacion,
            editor=editor,
            estado=estado,
            fecha_publicacion=fecha_publicacion,
            issn=data.get('issn', '').strip() or None,
            isbn=data.get('isbn', '').strip() or None,
            doi=data.get('doi', '').strip() or None,
            url_externa=data.get('url_externa', '').strip() or None,
            metadata=data.get('metadata') or None,
        )
        
        publicacion.full_clean()
        publicacion.save()
        
        # Procesar proyectos asociados
        for idx, proy_data in enumerate(proyectos_data):
            proyecto_id = proy_data.get('id') if isinstance(proy_data, dict) else proy_data
            if proyecto_id:
                try:
                    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
                    orden = proy_data.get('orden', idx) if isinstance(proy_data, dict) else idx
                    rol = proy_data.get('rol_en_publicacion', '') if isinstance(proy_data, dict) else ''
                    PublicacionProyecto.objects.create(
                        publicacion=publicacion,
                        proyecto=proyecto,
                        orden=orden,
                        rol_en_publicacion=rol or None
                    )
                except:
                    pass  # Ignorar proyectos inválidos
        
        # Procesar categorías asociadas
        categorias = data.get('categorias', [])
        if categorias:
            categoria_ids = [cat.get('id') if isinstance(cat, dict) else cat for cat in categorias]
            publicacion.categorias.set(Categoria.objects.filter(id__in=categoria_ids))
        
        # Procesar etiquetas asociadas
        etiquetas = data.get('etiquetas', [])
        if etiquetas:
            etiqueta_ids = [etq.get('id') if isinstance(etq, dict) else etq for etq in etiquetas]
            publicacion.etiquetas.set(Etiqueta.objects.filter(id__in=etiqueta_ids))
        
        # Retornar los datos de la publicación creada
        primer_proyecto_asociado = publicacion.proyectos.first()
        titulo_display = primer_proyecto_asociado.titulo if primer_proyecto_asociado else "Publicación sin título"
        descripcion_display = primer_proyecto_asociado.resumen if primer_proyecto_asociado else ""

        pub_dict = {
            'id': publicacion.id,
            'titulo': titulo_display,
            'slug': publicacion.slug,
            'descripcion': descripcion_display,
            'tipo_publicacion': publicacion.tipo_publicacion,
            'tipo_publicacion_display': publicacion.get_tipo_publicacion_display(),
            'editor_id': publicacion.editor.id,
            'editor_nombre': publicacion.editor.get_full_name() or publicacion.editor.username,
            'estado': publicacion.estado,
            'estado_display': publicacion.get_estado_display(),
            'fecha_creacion': publicacion.fecha_creacion.isoformat() if publicacion.fecha_creacion else None,
            'fecha_publicacion': publicacion.fecha_publicacion.isoformat() if publicacion.fecha_publicacion else None,
            'issn': publicacion.issn or '',
            'isbn': publicacion.isbn or '',
            'doi': publicacion.doi or '',
            'url_externa': publicacion.url_externa or '',
            'proyectos_count': publicacion.proyectos.count(),
            'categorias_count': publicacion.categorias.count(),
            'etiquetas_count': publicacion.etiquetas.count(),
        }
        
        return JsonResponse({
            'success': True,
            'data': pub_dict,
            'message': 'Publicación creada exitosamente'
        })
    except ValidationError as e:
        return JsonResponse({
            'success': False,
            'error': 'Error de validación: ' + str(e)
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
@transaction.atomic
def publicacion_update(request, publicacion_id):
    """Actualiza una publicación existente"""
    try:
        data = json.loads(request.body)
        if data.get('_method') != 'PUT':
            return JsonResponse({
                'success': False,
                'error': 'Método no permitido'
            }, status=405)
        
        publicacion = get_object_or_404(Publicacion, id=publicacion_id)
        
        # Actualizar campos
        tipo_publicacion = data.get('tipo_publicacion', publicacion.tipo_publicacion)
        if tipo_publicacion in [choice[0] for choice in Publicacion.TIPO_PUBLICACION_CHOICES]:
            publicacion.tipo_publicacion = tipo_publicacion
        
        estado = data.get('estado', publicacion.estado)
        if estado in [choice[0] for choice in Publicacion.ESTADO_CHOICES]:
            publicacion.estado = estado
        
        # Actualizar editor
        editor_id = data.get('editor_id')
        if editor_id:
            editor = get_object_or_404(User, id=editor_id)
            publicacion.editor = editor
        
        # Procesar fecha de publicación
        fecha_publicacion = data.get('fecha_publicacion')
        if fecha_publicacion:
            try:
                fecha_publicacion = datetime.fromisoformat(fecha_publicacion.replace('Z', '+00:00'))
                publicacion.fecha_publicacion = fecha_publicacion
            except:
                pass
        else:
            publicacion.fecha_publicacion = None
        
        publicacion.issn = data.get('issn', '').strip() or None
        publicacion.isbn = data.get('isbn', '').strip() or None
        publicacion.doi = data.get('doi', '').strip() or None
        publicacion.url_externa = data.get('url_externa', '').strip() or None
        publicacion.metadata = data.get('metadata') or None
        
        publicacion.full_clean()
        publicacion.save()
        
        # Actualizar proyectos asociados
        proyectos = data.get('proyectos', [])
        if proyectos is not None:  # Si se envía la lista, actualizar
            # Eliminar relaciones existentes
            PublicacionProyecto.objects.filter(publicacion=publicacion).delete()
            
            # Crear nuevas relaciones
            for idx, proy_data in enumerate(proyectos):
                proyecto_id = proy_data.get('id') if isinstance(proy_data, dict) else proy_data
                if proyecto_id:
                    try:
                        proyecto = get_object_or_404(Proyecto, id=proyecto_id)
                        orden = proy_data.get('orden', idx) if isinstance(proy_data, dict) else idx
                        rol = proy_data.get('rol_en_publicacion', '') if isinstance(proy_data, dict) else ''
                        PublicacionProyecto.objects.create(
                            publicacion=publicacion,
                            proyecto=proyecto,
                            orden=orden,
                            rol_en_publicacion=rol or None
                        )
                    except:
                        pass
        
        # Actualizar categorías asociadas
        categorias = data.get('categorias', [])
        if categorias is not None:
            categoria_ids = [cat.get('id') if isinstance(cat, dict) else cat for cat in categorias]
            publicacion.categorias.set(Categoria.objects.filter(id__in=categoria_ids))
        
        # Actualizar etiquetas asociadas
        etiquetas = data.get('etiquetas', [])
        if etiquetas is not None:
            etiqueta_ids = [etq.get('id') if isinstance(etq, dict) else etq for etq in etiquetas]
            publicacion.etiquetas.set(Etiqueta.objects.filter(id__in=etiqueta_ids))
        
        # Retornar los datos actualizados
        primer_proyecto_asociado = publicacion.proyectos.first()
        titulo_display = primer_proyecto_asociado.titulo if primer_proyecto_asociado else "Publicación sin título"
        descripcion_display = primer_proyecto_asociado.resumen if primer_proyecto_asociado else ""
        editor_nombre = publicacion.editor.get_full_name() if publicacion.editor.get_full_name() else publicacion.editor.username
        
        pub_dict = {
            'id': publicacion.id,
            'titulo': titulo_display,
            'slug': publicacion.slug,
            'descripcion': descripcion_display,
            'tipo_publicacion': publicacion.tipo_publicacion,
            'tipo_publicacion_display': publicacion.get_tipo_publicacion_display(),
            'editor_id': publicacion.editor.id,
            'editor_nombre': editor_nombre,
            'estado': publicacion.estado,
            'estado_display': publicacion.get_estado_display(),
            'fecha_creacion': publicacion.fecha_creacion.isoformat() if publicacion.fecha_creacion else None,
            'fecha_publicacion': publicacion.fecha_publicacion.isoformat() if publicacion.fecha_publicacion else None,
            'issn': publicacion.issn or '',
            'isbn': publicacion.isbn or '',
            'doi': publicacion.doi or '',
            'url_externa': publicacion.url_externa or '',
            'proyectos_count': publicacion.proyectos.count(),
            'categorias_count': publicacion.categorias.count(),
            'etiquetas_count': publicacion.etiquetas.count(),
        }
        
        return JsonResponse({
            'success': True,
            'data': pub_dict,
            'message': 'Publicación actualizada exitosamente'
        })
    except ValidationError as e:
        return JsonResponse({
            'success': False,
            'error': 'Error de validación: ' + str(e)
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
@transaction.atomic
def publicacion_delete(request, publicacion_id):
    """Elimina una publicación"""
    try:
        data = json.loads(request.body) if request.body else {}
        if data.get('_method') != 'DELETE':
            return JsonResponse({
                'success': False,
                'error': 'Método no permitido'
            }, status=405)
        
        publicacion = get_object_or_404(Publicacion, id=publicacion_id)
        titulo = publicacion.titulo
        publicacion.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Publicación "{titulo}" eliminada exitosamente'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ============================================================================
# VISTAS AUXILIARES PARA SELECTS
# ============================================================================

@login_required
@require_http_methods(["GET"])
def proyectos_for_select(request):
    """Obtiene la lista de proyectos para select"""
    proyectos = Proyecto.objects.all().select_related('tipo_proyecto')
    proyectos_data = []
    
    for proyecto in proyectos:
        proyectos_data.append({
            'id': proyecto.id,
            'titulo': proyecto.titulo,
            'tipo_proyecto': proyecto.tipo_proyecto.nombre if proyecto.tipo_proyecto else '',
        })
    
    return JsonResponse({
        'success': True,
        'data': proyectos_data
    })


@login_required
@require_http_methods(["GET"])
def categorias_for_select(request):
    """Obtiene la lista de categorías para select"""
    categorias = Categoria.objects.all()
    categorias_data = []
    
    for categoria in categorias:
        categorias_data.append({
            'id': categoria.id,
            'nombre': categoria.nombre,
            'ruta_completa': categoria.ruta_completa or categoria.nombre,
        })
    
    return JsonResponse({
        'success': True,
        'data': categorias_data
    })


@login_required
@require_http_methods(["GET"])
def etiquetas_for_select(request):
    """Obtiene la lista de etiquetas para select"""
    etiquetas = Etiqueta.objects.all()
    etiquetas_data = []
    
    for etiqueta in etiquetas:
        etiquetas_data.append({
            'id': etiqueta.id,
            'nombre': etiqueta.nombre,
            'color': etiqueta.color or '',
        })
    
    return JsonResponse({
        'success': True,
        'data': etiquetas_data
    })


@login_required
@require_http_methods(["GET"])
def generar_slug_preview(request):
    """Genera un slug de previsualización para una nueva publicación."""
    try:
        proyecto_id = request.GET.get('proyecto_id')
        if not proyecto_id:
            return JsonResponse({'success': False, 'error': 'Se requiere un ID de proyecto.'}, status=400)

        # Generar un slug potencial (no se guarda, solo para previsualización)
        timestamp = int(datetime.now().timestamp())
        slug_preview = f"{timestamp}-{proyecto_id}"
        
        return JsonResponse({
            'success': True,
            'slug_preview': slug_preview
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def usuarios_for_select(request):
    """Obtiene la lista de usuarios para select (editores)"""
    usuarios = User.objects.filter(is_active=True)
    usuarios_data = []
    
    for usuario in usuarios:
        usuarios_data.append({
            'id': usuario.id,
            'nombre': usuario.get_full_name() or usuario.username,
            'username': usuario.username,
            'email': usuario.email or '',
        })
    
    return JsonResponse({
        'success': True,
        'data': usuarios_data
    })
