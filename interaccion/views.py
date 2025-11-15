from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.contrib.auth.models import User
import json
from .models import Comentario, Valoracion, Cita, ReferenciaBibliografica
from repositorio.models import Documento


@login_required
@ensure_csrf_cookie
@require_http_methods(["GET"])
def index(request):
    """Vista principal de interacción"""
    # Verificar permisos
    if not (request.user.has_perm('interaccion.view_comentario') or 
            request.user.has_perm('interaccion.view_valoracion') or 
            request.user.has_perm('interaccion.view_cita') or
            request.user.has_perm('interaccion.view_referenciabibliografica') or
            request.user.is_superuser):
        messages.warning(request, 'No tienes permisos para acceder a interacción.')
        return redirect('usuarios:panel')
    return render(request, 'interaccion/index.html')


# ============================================================================
# VISTAS AUXILIARES PARA SELECTS
# ============================================================================

@login_required
@require_http_methods(["GET"])
def documentos_for_select(request):
    """Obtiene los documentos para usar en selects"""
    try:
        documentos = Documento.objects.select_related('proyecto', 'tipo_recurso', 'estado').all()
        documentos_data = []
        
        for documento in documentos:
            titulo = documento.get_titulo() if hasattr(documento, 'get_titulo') else (documento.titulo or f'Documento #{documento.id}')
            documentos_data.append({
                'id': documento.id,
                'text': titulo,
                'handle': documento.handle or '',
                'proyecto_titulo': documento.proyecto.titulo if documento.proyecto else '',
            })
        
        return JsonResponse({
            'success': True,
            'data': documentos_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener documentos: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def usuarios_for_select(request):
    """Obtiene los usuarios activos para usar en selects"""
    try:
        usuarios = User.objects.filter(is_active=True).order_by('first_name', 'last_name', 'username')
        usuarios_data = []
        
        for usuario in usuarios:
            nombre_completo = usuario.get_full_name() or usuario.username
            usuarios_data.append({
                'id': usuario.id,
                'text': nombre_completo,
                'username': usuario.username,
                'email': usuario.email or '',
            })
        
        return JsonResponse({
            'success': True,
            'data': usuarios_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener usuarios: {str(e)}'
        }, status=500)


# ============================================================================
# VISTAS PARA COMENTARIOS
# ============================================================================

@login_required
@require_http_methods(["GET"])
def comentarios_list(request):
    """Lista todos los comentarios en formato JSON"""
    comentarios = Comentario.objects.select_related('documento', 'usuario', 'comentario_padre').all()
    comentarios_data = []
    
    for comentario in comentarios:
        comentario_dict = {
            'id': comentario.id,
            'documento_id': comentario.documento.id,
            'documento_titulo': comentario.documento.get_titulo() if hasattr(comentario.documento, 'get_titulo') else (comentario.documento.titulo or f'Documento #{comentario.documento.id}'),
            'usuario_id': comentario.usuario.id,
            'usuario_nombre': comentario.usuario.get_full_name() or comentario.usuario.username,
            'comentario_padre_id': comentario.comentario_padre.id if comentario.comentario_padre else None,
            'comentario_padre_preview': comentario.comentario_padre.contenido[:50] + '...' if comentario.comentario_padre else None,
            'contenido': comentario.contenido,
            'es_moderado': comentario.es_moderado,
            'es_publico': comentario.es_publico,
            'fecha_creacion': comentario.fecha_creacion.isoformat() if comentario.fecha_creacion else None,
            'fecha_actualizacion': comentario.fecha_actualizacion.isoformat() if comentario.fecha_actualizacion else None,
            'respuestas_count': comentario.respuestas.count(),
        }
        comentarios_data.append(comentario_dict)
    
    return JsonResponse({
        'success': True,
        'data': comentarios_data,
        'total': len(comentarios_data)
    })


@login_required
@require_http_methods(["POST"])
def comentario_create(request):
    """Crea un nuevo comentario"""
    try:
        data = json.loads(request.body)
        
        # Validar campos requeridos
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
        
        # Usuario: usar el usuario autenticado o el especificado
        usuario_id = data.get('usuario_id')
        if usuario_id:
            usuario = get_object_or_404(User, id=usuario_id)
        else:
            usuario = request.user
        
        # Comentario padre (opcional)
        comentario_padre_id = data.get('comentario_padre_id')
        comentario_padre = None
        if comentario_padre_id:
            comentario_padre = get_object_or_404(Comentario, id=comentario_padre_id)
        
        # Crear el comentario
        comentario = Comentario(
            documento=documento,
            usuario=usuario,
            comentario_padre=comentario_padre,
            contenido=contenido,
            es_moderado=data.get('es_moderado', False),
            es_publico=data.get('es_publico', True),
        )
        
        comentario.full_clean()
        comentario.save()
        
        # Retornar los datos del comentario creado
        comentario_dict = {
            'id': comentario.id,
            'documento_id': comentario.documento.id,
            'documento_titulo': comentario.documento.get_titulo() if hasattr(comentario.documento, 'get_titulo') else (comentario.documento.titulo or f'Documento #{comentario.documento.id}'),
            'usuario_id': comentario.usuario.id,
            'usuario_nombre': comentario.usuario.get_full_name() or comentario.usuario.username,
            'comentario_padre_id': comentario.comentario_padre.id if comentario.comentario_padre else None,
            'contenido': comentario.contenido,
            'es_moderado': comentario.es_moderado,
            'es_publico': comentario.es_publico,
            'fecha_creacion': comentario.fecha_creacion.isoformat() if comentario.fecha_creacion else None,
            'respuestas_count': comentario.respuestas.count(),
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Comentario creado exitosamente',
            'data': comentario_dict
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
            'error': f'Error al crear comentario: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def comentario_detail(request, comentario_id):
    """Obtiene los detalles de un comentario"""
    try:
        comentario = get_object_or_404(
            Comentario.objects.select_related('documento', 'usuario', 'comentario_padre'),
            id=comentario_id
        )
        
        comentario_dict = {
            'id': comentario.id,
            'documento_id': comentario.documento.id,
            'documento_titulo': comentario.documento.get_titulo() if hasattr(comentario.documento, 'get_titulo') else (comentario.documento.titulo or f'Documento #{comentario.documento.id}'),
            'usuario_id': comentario.usuario.id,
            'usuario_nombre': comentario.usuario.get_full_name() or comentario.usuario.username,
            'comentario_padre_id': comentario.comentario_padre.id if comentario.comentario_padre else None,
            'contenido': comentario.contenido,
            'es_moderado': comentario.es_moderado,
            'es_publico': comentario.es_publico,
            'fecha_creacion': comentario.fecha_creacion.isoformat() if comentario.fecha_creacion else None,
            'fecha_actualizacion': comentario.fecha_actualizacion.isoformat() if comentario.fecha_actualizacion else None,
            'respuestas_count': comentario.respuestas.count(),
        }
        
        return JsonResponse({
            'success': True,
            'data': comentario_dict
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener comentario: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "PUT"])
def comentario_update(request, comentario_id):
    """Actualiza un comentario existente"""
    try:
        comentario = get_object_or_404(Comentario, id=comentario_id)
        
        # Manejar tanto POST con _method como PUT directo
        if request.method == 'POST':
            data = json.loads(request.body)
            if data.get('_method') != 'PUT':
                return JsonResponse({
                    'success': False,
                    'error': 'Método no permitido'
                }, status=405)
        else:
            data = json.loads(request.body)
        
        # Validar contenido
        contenido = data.get('contenido', '').strip()
        if not contenido:
            return JsonResponse({
                'success': False,
                'error': 'El contenido es obligatorio'
            }, status=400)
        
        # Actualizar campos
        comentario.contenido = contenido
        comentario.es_moderado = data.get('es_moderado', comentario.es_moderado)
        comentario.es_publico = data.get('es_publico', comentario.es_publico)
        
        comentario.full_clean()
        comentario.save()
        
        # Retornar los datos actualizados
        comentario_dict = {
            'id': comentario.id,
            'documento_id': comentario.documento.id,
            'documento_titulo': comentario.documento.get_titulo() if hasattr(comentario.documento, 'get_titulo') else (comentario.documento.titulo or f'Documento #{comentario.documento.id}'),
            'usuario_id': comentario.usuario.id,
            'usuario_nombre': comentario.usuario.get_full_name() or comentario.usuario.username,
            'contenido': comentario.contenido,
            'es_moderado': comentario.es_moderado,
            'es_publico': comentario.es_publico,
            'fecha_actualizacion': comentario.fecha_actualizacion.isoformat() if comentario.fecha_actualizacion else None,
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Comentario actualizado exitosamente',
            'data': comentario_dict
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
            'error': f'Error al actualizar comentario: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "DELETE"])
def comentario_delete(request, comentario_id):
    """Elimina un comentario"""
    try:
        comentario = get_object_or_404(Comentario, id=comentario_id)
        
        # Manejar tanto POST con _method como DELETE directo
        if request.method == 'POST':
            data = json.loads(request.body) if request.body else {}
            if data.get('_method') != 'DELETE':
                return JsonResponse({
                    'success': False,
                    'error': 'Método no permitido'
                }, status=405)
        
        # Eliminar el comentario (esto también eliminará las respuestas por CASCADE)
        comentario_contenido = comentario.contenido[:50] + '...' if len(comentario.contenido) > 50 else comentario.contenido
        comentario.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Comentario eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al eliminar comentario: {str(e)}'
        }, status=500)


# ============================================================================
# VISTAS PARA VALORACIONES
# ============================================================================

@login_required
@require_http_methods(["GET"])
def valoraciones_list(request):
    """Lista todas las valoraciones en formato JSON"""
    valoraciones = Valoracion.objects.select_related('documento', 'usuario').all()
    valoraciones_data = []
    
    for valoracion in valoraciones:
        valoracion_dict = {
            'id': valoracion.id,
            'documento_id': valoracion.documento.id,
            'documento_titulo': valoracion.documento.get_titulo() if hasattr(valoracion.documento, 'get_titulo') else (valoracion.documento.titulo or f'Documento #{valoracion.documento.id}'),
            'usuario_id': valoracion.usuario.id,
            'usuario_nombre': valoracion.usuario.get_full_name() or valoracion.usuario.username,
            'calificacion': valoracion.calificacion,
            'comentario': valoracion.comentario or '',
            'fecha': valoracion.fecha.isoformat() if valoracion.fecha else None,
        }
        valoraciones_data.append(valoracion_dict)
    
    return JsonResponse({
        'success': True,
        'data': valoraciones_data,
        'total': len(valoraciones_data)
    })


@login_required
@require_http_methods(["POST"])
def valoracion_create(request):
    """Crea una nueva valoración"""
    try:
        data = json.loads(request.body)
        
        # Validar campos requeridos
        documento_id = data.get('documento_id')
        if not documento_id:
            return JsonResponse({
                'success': False,
                'error': 'El documento es obligatorio'
            }, status=400)
        
        documento = get_object_or_404(Documento, id=documento_id)
        
        calificacion = data.get('calificacion')
        if not calificacion:
            return JsonResponse({
                'success': False,
                'error': 'La calificación es obligatoria'
            }, status=400)
        
        try:
            calificacion = int(calificacion)
            if calificacion < 1 or calificacion > 5:
                return JsonResponse({
                    'success': False,
                    'error': 'La calificación debe estar entre 1 y 5'
                }, status=400)
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'error': 'La calificación debe ser un número'
            }, status=400)
        
        # Usuario: usar el usuario autenticado o el especificado
        usuario_id = data.get('usuario_id')
        if usuario_id:
            usuario = get_object_or_404(User, id=usuario_id)
        else:
            usuario = request.user
        
        # Verificar que el usuario no haya valorado ya este documento
        if Valoracion.objects.filter(documento=documento, usuario=usuario).exists():
            return JsonResponse({
                'success': False,
                'error': 'Ya has valorado este documento'
            }, status=400)
        
        # Crear la valoración
        valoracion = Valoracion(
            documento=documento,
            usuario=usuario,
            calificacion=calificacion,
            comentario=data.get('comentario', '').strip() or None,
        )
        
        valoracion.full_clean()
        valoracion.save()
        
        # Retornar los datos de la valoración creada
        valoracion_dict = {
            'id': valoracion.id,
            'documento_id': valoracion.documento.id,
            'documento_titulo': valoracion.documento.get_titulo() if hasattr(valoracion.documento, 'get_titulo') else (valoracion.documento.titulo or f'Documento #{valoracion.documento.id}'),
            'usuario_id': valoracion.usuario.id,
            'usuario_nombre': valoracion.usuario.get_full_name() or valoracion.usuario.username,
            'calificacion': valoracion.calificacion,
            'comentario': valoracion.comentario or '',
            'fecha': valoracion.fecha.isoformat() if valoracion.fecha else None,
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Valoración creada exitosamente',
            'data': valoracion_dict
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
            'error': f'Error al crear valoración: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def valoracion_detail(request, valoracion_id):
    """Obtiene los detalles de una valoración"""
    try:
        valoracion = get_object_or_404(
            Valoracion.objects.select_related('documento', 'usuario'),
            id=valoracion_id
        )
        
        valoracion_dict = {
            'id': valoracion.id,
            'documento_id': valoracion.documento.id,
            'documento_titulo': valoracion.documento.get_titulo() if hasattr(valoracion.documento, 'get_titulo') else (valoracion.documento.titulo or f'Documento #{valoracion.documento.id}'),
            'usuario_id': valoracion.usuario.id,
            'usuario_nombre': valoracion.usuario.get_full_name() or valoracion.usuario.username,
            'calificacion': valoracion.calificacion,
            'comentario': valoracion.comentario or '',
            'fecha': valoracion.fecha.isoformat() if valoracion.fecha else None,
        }
        
        return JsonResponse({
            'success': True,
            'data': valoracion_dict
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener valoración: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "PUT"])
def valoracion_update(request, valoracion_id):
    """Actualiza una valoración existente"""
    try:
        valoracion = get_object_or_404(Valoracion, id=valoracion_id)
        
        # Manejar tanto POST con _method como PUT directo
        if request.method == 'POST':
            data = json.loads(request.body)
            if data.get('_method') != 'PUT':
                return JsonResponse({
                    'success': False,
                    'error': 'Método no permitido'
                }, status=405)
        else:
            data = json.loads(request.body)
        
        # Validar calificación
        calificacion = data.get('calificacion')
        if calificacion:
            try:
                calificacion = int(calificacion)
                if calificacion < 1 or calificacion > 5:
                    return JsonResponse({
                        'success': False,
                        'error': 'La calificación debe estar entre 1 y 5'
                    }, status=400)
                valoracion.calificacion = calificacion
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': 'La calificación debe ser un número'
                }, status=400)
        
        # Actualizar comentario
        if 'comentario' in data:
            valoracion.comentario = data.get('comentario', '').strip() or None
        
        valoracion.full_clean()
        valoracion.save()
        
        # Retornar los datos actualizados
        valoracion_dict = {
            'id': valoracion.id,
            'documento_id': valoracion.documento.id,
            'documento_titulo': valoracion.documento.get_titulo() if hasattr(valoracion.documento, 'get_titulo') else (valoracion.documento.titulo or f'Documento #{valoracion.documento.id}'),
            'usuario_id': valoracion.usuario.id,
            'usuario_nombre': valoracion.usuario.get_full_name() or valoracion.usuario.username,
            'calificacion': valoracion.calificacion,
            'comentario': valoracion.comentario or '',
            'fecha': valoracion.fecha.isoformat() if valoracion.fecha else None,
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Valoración actualizada exitosamente',
            'data': valoracion_dict
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
            'error': f'Error al actualizar valoración: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "DELETE"])
def valoracion_delete(request, valoracion_id):
    """Elimina una valoración"""
    try:
        valoracion = get_object_or_404(Valoracion, id=valoracion_id)
        
        # Manejar tanto POST con _method como DELETE directo
        if request.method == 'POST':
            data = json.loads(request.body) if request.body else {}
            if data.get('_method') != 'DELETE':
                return JsonResponse({
                    'success': False,
                    'error': 'Método no permitido'
                }, status=405)
        
        # Eliminar la valoración
        valoracion.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Valoración eliminada exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al eliminar valoración: {str(e)}'
        }, status=500)


# ============================================================================
# VISTAS PARA CITAS
# ============================================================================

@login_required
@require_http_methods(["GET"])
def citas_list(request):
    """Lista todas las citas en formato JSON"""
    citas = Cita.objects.select_related('documento_citado', 'documento_que_cita').all()
    citas_data = []
    
    for cita in citas:
        cita_dict = {
            'id': cita.id,
            'documento_citado_id': cita.documento_citado.id,
            'documento_citado_titulo': cita.documento_citado.get_titulo() if hasattr(cita.documento_citado, 'get_titulo') else (cita.documento_citado.titulo or f'Documento #{cita.documento_citado.id}'),
            'documento_que_cita_id': cita.documento_que_cita.id,
            'documento_que_cita_titulo': cita.documento_que_cita.get_titulo() if hasattr(cita.documento_que_cita, 'get_titulo') else (cita.documento_que_cita.titulo or f'Documento #{cita.documento_que_cita.id}'),
            'contexto': cita.contexto or '',
            'fecha_citacion': cita.fecha_citacion.isoformat() if cita.fecha_citacion else None,
        }
        citas_data.append(cita_dict)
    
    return JsonResponse({
        'success': True,
        'data': citas_data,
        'total': len(citas_data)
    })


@login_required
@require_http_methods(["POST"])
def cita_create(request):
    """Crea una nueva cita"""
    try:
        data = json.loads(request.body)
        
        # Validar campos requeridos
        documento_citado_id = data.get('documento_citado_id')
        documento_que_cita_id = data.get('documento_que_cita_id')
        
        if not documento_citado_id or not documento_que_cita_id:
            return JsonResponse({
                'success': False,
                'error': 'Ambos documentos son obligatorios'
            }, status=400)
        
        if documento_citado_id == documento_que_cita_id:
            return JsonResponse({
                'success': False,
                'error': 'Un documento no puede citarse a sí mismo'
            }, status=400)
        
        documento_citado = get_object_or_404(Documento, id=documento_citado_id)
        documento_que_cita = get_object_or_404(Documento, id=documento_que_cita_id)
        
        # Verificar que no exista ya esta cita
        if Cita.objects.filter(documento_citado=documento_citado, documento_que_cita=documento_que_cita).exists():
            return JsonResponse({
                'success': False,
                'error': 'Esta cita ya existe'
            }, status=400)
        
        # Crear la cita
        cita = Cita(
            documento_citado=documento_citado,
            documento_que_cita=documento_que_cita,
            contexto=data.get('contexto', '').strip() or None,
        )
        
        cita.full_clean()
        cita.save()
        
        # Retornar los datos de la cita creada
        cita_dict = {
            'id': cita.id,
            'documento_citado_id': cita.documento_citado.id,
            'documento_citado_titulo': cita.documento_citado.get_titulo() if hasattr(cita.documento_citado, 'get_titulo') else (cita.documento_citado.titulo or f'Documento #{cita.documento_citado.id}'),
            'documento_que_cita_id': cita.documento_que_cita.id,
            'documento_que_cita_titulo': cita.documento_que_cita.get_titulo() if hasattr(cita.documento_que_cita, 'get_titulo') else (cita.documento_que_cita.titulo or f'Documento #{cita.documento_que_cita.id}'),
            'contexto': cita.contexto or '',
            'fecha_citacion': cita.fecha_citacion.isoformat() if cita.fecha_citacion else None,
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Cita creada exitosamente',
            'data': cita_dict
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
            'error': f'Error al crear cita: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def cita_detail(request, cita_id):
    """Obtiene los detalles de una cita"""
    try:
        cita = get_object_or_404(
            Cita.objects.select_related('documento_citado', 'documento_que_cita'),
            id=cita_id
        )
        
        cita_dict = {
            'id': cita.id,
            'documento_citado_id': cita.documento_citado.id,
            'documento_citado_titulo': cita.documento_citado.get_titulo() if hasattr(cita.documento_citado, 'get_titulo') else (cita.documento_citado.titulo or f'Documento #{cita.documento_citado.id}'),
            'documento_que_cita_id': cita.documento_que_cita.id,
            'documento_que_cita_titulo': cita.documento_que_cita.get_titulo() if hasattr(cita.documento_que_cita, 'get_titulo') else (cita.documento_que_cita.titulo or f'Documento #{cita.documento_que_cita.id}'),
            'contexto': cita.contexto or '',
            'fecha_citacion': cita.fecha_citacion.isoformat() if cita.fecha_citacion else None,
        }
        
        return JsonResponse({
            'success': True,
            'data': cita_dict
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener cita: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "PUT"])
def cita_update(request, cita_id):
    """Actualiza una cita existente"""
    try:
        cita = get_object_or_404(Cita, id=cita_id)
        
        # Manejar tanto POST con _method como PUT directo
        if request.method == 'POST':
            data = json.loads(request.body)
            if data.get('_method') != 'PUT':
                return JsonResponse({
                    'success': False,
                    'error': 'Método no permitido'
                }, status=405)
        else:
            data = json.loads(request.body)
        
        # Actualizar contexto
        if 'contexto' in data:
            cita.contexto = data.get('contexto', '').strip() or None
        
        cita.full_clean()
        cita.save()
        
        # Retornar los datos actualizados
        cita_dict = {
            'id': cita.id,
            'documento_citado_id': cita.documento_citado.id,
            'documento_citado_titulo': cita.documento_citado.get_titulo() if hasattr(cita.documento_citado, 'get_titulo') else (cita.documento_citado.titulo or f'Documento #{cita.documento_citado.id}'),
            'documento_que_cita_id': cita.documento_que_cita.id,
            'documento_que_cita_titulo': cita.documento_que_cita.get_titulo() if hasattr(cita.documento_que_cita, 'get_titulo') else (cita.documento_que_cita.titulo or f'Documento #{cita.documento_que_cita.id}'),
            'contexto': cita.contexto or '',
            'fecha_citacion': cita.fecha_citacion.isoformat() if cita.fecha_citacion else None,
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Cita actualizada exitosamente',
            'data': cita_dict
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
            'error': f'Error al actualizar cita: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "DELETE"])
def cita_delete(request, cita_id):
    """Elimina una cita"""
    try:
        cita = get_object_or_404(Cita, id=cita_id)
        
        # Manejar tanto POST con _method como DELETE directo
        if request.method == 'POST':
            data = json.loads(request.body) if request.body else {}
            if data.get('_method') != 'DELETE':
                return JsonResponse({
                    'success': False,
                    'error': 'Método no permitido'
                }, status=405)
        
        # Eliminar la cita
        cita.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Cita eliminada exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al eliminar cita: {str(e)}'
        }, status=500)


# ============================================================================
# VISTAS PARA REFERENCIAS BIBLIOGRÁFICAS
# ============================================================================

@login_required
@require_http_methods(["GET"])
def referencias_list(request):
    """Lista todas las referencias bibliográficas en formato JSON"""
    referencias = ReferenciaBibliografica.objects.select_related('documento').all()
    referencias_data = []
    
    for referencia in referencias:
        referencia_dict = {
            'id': referencia.id,
            'documento_id': referencia.documento.id,
            'documento_titulo': referencia.documento.get_titulo() if hasattr(referencia.documento, 'get_titulo') else (referencia.documento.titulo or f'Documento #{referencia.documento.id}'),
            'tipo': referencia.tipo,
            'tipo_display': referencia.get_tipo_display(),
            'titulo': referencia.titulo,
            'autores': referencia.autores or '',
            'año': referencia.año,
            'doi': referencia.doi or '',
            'url': referencia.url or '',
            'cita_completa': referencia.cita_completa or '',
            'orden': referencia.orden,
        }
        referencias_data.append(referencia_dict)
    
    return JsonResponse({
        'success': True,
        'data': referencias_data,
        'total': len(referencias_data)
    })


@login_required
@require_http_methods(["POST"])
def referencia_create(request):
    """Crea una nueva referencia bibliográfica"""
    try:
        data = json.loads(request.body)
        
        # Validar campos requeridos
        documento_id = data.get('documento_id')
        if not documento_id:
            return JsonResponse({
                'success': False,
                'error': 'El documento es obligatorio'
            }, status=400)
        
        documento = get_object_or_404(Documento, id=documento_id)
        
        titulo = data.get('titulo', '').strip()
        if not titulo:
            return JsonResponse({
                'success': False,
                'error': 'El título es obligatorio'
            }, status=400)
        
        # Crear la referencia
        referencia = ReferenciaBibliografica(
            documento=documento,
            tipo=data.get('tipo', 'otros'),
            titulo=titulo,
            autores=data.get('autores', '').strip() or None,
            año=data.get('año') or None,
            doi=data.get('doi', '').strip() or None,
            url=data.get('url', '').strip() or None,
            cita_completa=data.get('cita_completa', '').strip() or None,
            orden=data.get('orden', 0),
        )
        
        referencia.full_clean()
        referencia.save()
        
        # Retornar los datos de la referencia creada
        referencia_dict = {
            'id': referencia.id,
            'documento_id': referencia.documento.id,
            'documento_titulo': referencia.documento.get_titulo() if hasattr(referencia.documento, 'get_titulo') else (referencia.documento.titulo or f'Documento #{referencia.documento.id}'),
            'tipo': referencia.tipo,
            'tipo_display': referencia.get_tipo_display(),
            'titulo': referencia.titulo,
            'autores': referencia.autores or '',
            'año': referencia.año,
            'doi': referencia.doi or '',
            'url': referencia.url or '',
            'cita_completa': referencia.cita_completa or '',
            'orden': referencia.orden,
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Referencia bibliográfica creada exitosamente',
            'data': referencia_dict
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
            'error': f'Error al crear referencia bibliográfica: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def referencia_detail(request, referencia_id):
    """Obtiene los detalles de una referencia bibliográfica"""
    try:
        referencia = get_object_or_404(
            ReferenciaBibliografica.objects.select_related('documento'),
            id=referencia_id
        )
        
        referencia_dict = {
            'id': referencia.id,
            'documento_id': referencia.documento.id,
            'documento_titulo': referencia.documento.get_titulo() if hasattr(referencia.documento, 'get_titulo') else (referencia.documento.titulo or f'Documento #{referencia.documento.id}'),
            'tipo': referencia.tipo,
            'tipo_display': referencia.get_tipo_display(),
            'titulo': referencia.titulo,
            'autores': referencia.autores or '',
            'año': referencia.año,
            'doi': referencia.doi or '',
            'url': referencia.url or '',
            'cita_completa': referencia.cita_completa or '',
            'orden': referencia.orden,
        }
        
        return JsonResponse({
            'success': True,
            'data': referencia_dict
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener referencia bibliográfica: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "PUT"])
def referencia_update(request, referencia_id):
    """Actualiza una referencia bibliográfica existente"""
    try:
        referencia = get_object_or_404(ReferenciaBibliografica, id=referencia_id)
        
        # Manejar tanto POST con _method como PUT directo
        if request.method == 'POST':
            data = json.loads(request.body)
            if data.get('_method') != 'PUT':
                return JsonResponse({
                    'success': False,
                    'error': 'Método no permitido'
                }, status=405)
        else:
            data = json.loads(request.body)
        
        # Validar título
        titulo = data.get('titulo', '').strip()
        if not titulo:
            return JsonResponse({
                'success': False,
                'error': 'El título es obligatorio'
            }, status=400)
        
        # Actualizar campos
        referencia.tipo = data.get('tipo', referencia.tipo)
        referencia.titulo = titulo
        referencia.autores = data.get('autores', '').strip() or None
        referencia.año = data.get('año') or None
        referencia.doi = data.get('doi', '').strip() or None
        referencia.url = data.get('url', '').strip() or None
        referencia.cita_completa = data.get('cita_completa', '').strip() or None
        referencia.orden = data.get('orden', referencia.orden)
        
        referencia.full_clean()
        referencia.save()
        
        # Retornar los datos actualizados
        referencia_dict = {
            'id': referencia.id,
            'documento_id': referencia.documento.id,
            'documento_titulo': referencia.documento.get_titulo() if hasattr(referencia.documento, 'get_titulo') else (referencia.documento.titulo or f'Documento #{referencia.documento.id}'),
            'tipo': referencia.tipo,
            'tipo_display': referencia.get_tipo_display(),
            'titulo': referencia.titulo,
            'autores': referencia.autores or '',
            'año': referencia.año,
            'doi': referencia.doi or '',
            'url': referencia.url or '',
            'cita_completa': referencia.cita_completa or '',
            'orden': referencia.orden,
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Referencia bibliográfica actualizada exitosamente',
            'data': referencia_dict
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
            'error': f'Error al actualizar referencia bibliográfica: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "DELETE"])
def referencia_delete(request, referencia_id):
    """Elimina una referencia bibliográfica"""
    try:
        referencia = get_object_or_404(ReferenciaBibliografica, id=referencia_id)
        
        # Manejar tanto POST con _method como DELETE directo
        if request.method == 'POST':
            data = json.loads(request.body) if request.body else {}
            if data.get('_method') != 'DELETE':
                return JsonResponse({
                    'success': False,
                    'error': 'Método no permitido'
                }, status=405)
        
        # Eliminar la referencia
        referencia_titulo = referencia.titulo[:50] + '...' if len(referencia.titulo) > 50 else referencia.titulo
        referencia.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Referencia bibliográfica eliminada exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al eliminar referencia bibliográfica: {str(e)}'
        }, status=500)
