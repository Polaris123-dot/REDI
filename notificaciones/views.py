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
from .models import TipoNotificacion, Notificacion
from repositorio.models import Documento


@login_required
@ensure_csrf_cookie
@require_http_methods(["GET"])
def index(request):
    """Vista principal de notificaciones"""
    # Verificar permisos
    if not (request.user.has_perm('notificaciones.view_tiponotificacion') or 
            request.user.has_perm('notificaciones.view_notificacion') or
            request.user.is_superuser):
        messages.warning(request, 'No tienes permisos para acceder a notificaciones.')
        return redirect('usuarios:panel')
    return render(request, 'notificaciones/index.html')


# ============================================================================
# VISTAS AUXILIARES PARA SELECTS
# ============================================================================

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
def tipos_for_select(request):
    """Obtiene los tipos de notificación para usar en selects"""
    try:
        tipos = TipoNotificacion.objects.all().order_by('nombre')
        tipos_data = []
        
        for tipo in tipos:
            tipos_data.append({
                'id': tipo.id,
                'text': tipo.nombre,
                'codigo': tipo.codigo,
                'descripcion': tipo.descripcion or '',
            })
        
        return JsonResponse({
            'success': True,
            'data': tipos_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener tipos de notificación: {str(e)}'
        }, status=500)


# ============================================================================
# VISTAS PARA TIPOS DE NOTIFICACIÓN
# ============================================================================

@login_required
@require_http_methods(["GET"])
def tipos_list(request):
    """Lista todos los tipos de notificación en formato JSON"""
    tipos = TipoNotificacion.objects.all()
    tipos_data = []
    
    for tipo in tipos:
        tipo_dict = {
            'id': tipo.id,
            'codigo': tipo.codigo,
            'nombre': tipo.nombre,
            'descripcion': tipo.descripcion or '',
            'plantilla': tipo.plantilla or '',
            'notificaciones_count': tipo.notificaciones.count(),
        }
        tipos_data.append(tipo_dict)
    
    return JsonResponse({
        'success': True,
        'data': tipos_data,
        'total': len(tipos_data)
    })


@login_required
@require_http_methods(["POST"])
def tipo_create(request):
    """Crea un nuevo tipo de notificación"""
    try:
        data = json.loads(request.body)
        
        # Validar campos requeridos
        codigo = data.get('codigo', '').strip()
        if not codigo:
            return JsonResponse({
                'success': False,
                'error': 'El código es obligatorio'
            }, status=400)
        
        nombre = data.get('nombre', '').strip()
        if not nombre:
            return JsonResponse({
                'success': False,
                'error': 'El nombre es obligatorio'
            }, status=400)
        
        # Verificar que el código no exista
        if TipoNotificacion.objects.filter(codigo=codigo).exists():
            return JsonResponse({
                'success': False,
                'error': 'Ya existe un tipo de notificación con este código'
            }, status=400)
        
        # Crear el tipo de notificación
        tipo = TipoNotificacion(
            codigo=codigo,
            nombre=nombre,
            descripcion=data.get('descripcion', '').strip() or None,
            plantilla=data.get('plantilla', '').strip() or None,
        )
        
        tipo.full_clean()
        tipo.save()
        
        # Retornar los datos del tipo creado
        tipo_dict = {
            'id': tipo.id,
            'codigo': tipo.codigo,
            'nombre': tipo.nombre,
            'descripcion': tipo.descripcion or '',
            'plantilla': tipo.plantilla or '',
            'notificaciones_count': tipo.notificaciones.count(),
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Tipo de notificación creado exitosamente',
            'data': tipo_dict
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
            'error': f'Error al crear tipo de notificación: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def tipo_detail(request, tipo_id):
    """Obtiene los detalles de un tipo de notificación"""
    try:
        tipo = get_object_or_404(TipoNotificacion, id=tipo_id)
        
        tipo_dict = {
            'id': tipo.id,
            'codigo': tipo.codigo,
            'nombre': tipo.nombre,
            'descripcion': tipo.descripcion or '',
            'plantilla': tipo.plantilla or '',
            'notificaciones_count': tipo.notificaciones.count(),
        }
        
        return JsonResponse({
            'success': True,
            'data': tipo_dict
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener tipo de notificación: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "PUT"])
def tipo_update(request, tipo_id):
    """Actualiza un tipo de notificación existente"""
    try:
        tipo = get_object_or_404(TipoNotificacion, id=tipo_id)
        
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
        
        # Validar código
        codigo = data.get('codigo', '').strip()
        if not codigo:
            return JsonResponse({
                'success': False,
                'error': 'El código es obligatorio'
            }, status=400)
        
        # Verificar que el código no exista en otro tipo
        if TipoNotificacion.objects.filter(codigo=codigo).exclude(id=tipo_id).exists():
            return JsonResponse({
                'success': False,
                'error': 'Ya existe otro tipo de notificación con este código'
            }, status=400)
        
        # Validar nombre
        nombre = data.get('nombre', '').strip()
        if not nombre:
            return JsonResponse({
                'success': False,
                'error': 'El nombre es obligatorio'
            }, status=400)
        
        # Actualizar campos
        tipo.codigo = codigo
        tipo.nombre = nombre
        tipo.descripcion = data.get('descripcion', '').strip() or None
        tipo.plantilla = data.get('plantilla', '').strip() or None
        
        tipo.full_clean()
        tipo.save()
        
        # Retornar los datos actualizados
        tipo_dict = {
            'id': tipo.id,
            'codigo': tipo.codigo,
            'nombre': tipo.nombre,
            'descripcion': tipo.descripcion or '',
            'plantilla': tipo.plantilla or '',
            'notificaciones_count': tipo.notificaciones.count(),
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Tipo de notificación actualizado exitosamente',
            'data': tipo_dict
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
            'error': f'Error al actualizar tipo de notificación: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "DELETE"])
def tipo_delete(request, tipo_id):
    """Elimina un tipo de notificación"""
    try:
        tipo = get_object_or_404(TipoNotificacion, id=tipo_id)
        
        # Manejar tanto POST con _method como DELETE directo
        if request.method == 'POST':
            data = json.loads(request.body) if request.body else {}
            if data.get('_method') != 'DELETE':
                return JsonResponse({
                    'success': False,
                    'error': 'Método no permitido'
                }, status=405)
        
        # Verificar si tiene notificaciones asociadas
        if tipo.notificaciones.exists():
            return JsonResponse({
                'success': False,
                'error': f'No se puede eliminar este tipo porque tiene {tipo.notificaciones.count()} notificación(es) asociada(s)'
            }, status=400)
        
        # Eliminar el tipo
        tipo_nombre = tipo.nombre
        tipo.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Tipo de notificación "{tipo_nombre}" eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al eliminar tipo de notificación: {str(e)}'
        }, status=500)


# ============================================================================
# VISTAS PARA NOTIFICACIONES
# ============================================================================

@login_required
@require_http_methods(["GET"])
def notificaciones_list(request):
    """Lista todas las notificaciones en formato JSON"""
    notificaciones = Notificacion.objects.select_related('usuario', 'tipo_notificacion', 'documento').all()
    notificaciones_data = []
    
    for notificacion in notificaciones:
        notificacion_dict = {
            'id': notificacion.id,
            'usuario_id': notificacion.usuario.id,
            'usuario_nombre': notificacion.usuario.get_full_name() or notificacion.usuario.username,
            'tipo_notificacion_id': notificacion.tipo_notificacion.id,
            'tipo_notificacion_nombre': notificacion.tipo_notificacion.nombre,
            'titulo': notificacion.titulo,
            'mensaje': notificacion.mensaje,
            'url_relacionada': notificacion.url_relacionada or '',
            'documento_id': notificacion.documento.id if notificacion.documento else None,
            'documento_titulo': notificacion.documento.get_titulo() if notificacion.documento and hasattr(notificacion.documento, 'get_titulo') else (notificacion.documento.titulo if notificacion.documento else None),
            'es_leida': notificacion.es_leida,
            'fecha_creacion': notificacion.fecha_creacion.isoformat() if notificacion.fecha_creacion else None,
        }
        notificaciones_data.append(notificacion_dict)
    
    return JsonResponse({
        'success': True,
        'data': notificaciones_data,
        'total': len(notificaciones_data)
    })


@login_required
@require_http_methods(["POST"])
def notificacion_create(request):
    """Crea una nueva notificación"""
    try:
        data = json.loads(request.body)
        
        # Validar campos requeridos
        usuario_id = data.get('usuario_id')
        if not usuario_id:
            return JsonResponse({
                'success': False,
                'error': 'El usuario es obligatorio'
            }, status=400)
        
        usuario = get_object_or_404(User, id=usuario_id)
        
        tipo_notificacion_id = data.get('tipo_notificacion_id')
        if not tipo_notificacion_id:
            return JsonResponse({
                'success': False,
                'error': 'El tipo de notificación es obligatorio'
            }, status=400)
        
        tipo_notificacion = get_object_or_404(TipoNotificacion, id=tipo_notificacion_id)
        
        titulo = data.get('titulo', '').strip()
        if not titulo:
            return JsonResponse({
                'success': False,
                'error': 'El título es obligatorio'
            }, status=400)
        
        mensaje = data.get('mensaje', '').strip()
        if not mensaje:
            return JsonResponse({
                'success': False,
                'error': 'El mensaje es obligatorio'
            }, status=400)
        
        # Documento (opcional)
        documento_id = data.get('documento_id')
        documento = None
        if documento_id:
            documento = get_object_or_404(Documento, id=documento_id)
        
        # Crear la notificación
        notificacion = Notificacion(
            usuario=usuario,
            tipo_notificacion=tipo_notificacion,
            titulo=titulo,
            mensaje=mensaje,
            url_relacionada=data.get('url_relacionada', '').strip() or None,
            documento=documento,
            es_leida=data.get('es_leida', False),
        )
        
        notificacion.full_clean()
        notificacion.save()
        
        # Retornar los datos de la notificación creada
        notificacion_dict = {
            'id': notificacion.id,
            'usuario_id': notificacion.usuario.id,
            'usuario_nombre': notificacion.usuario.get_full_name() or notificacion.usuario.username,
            'tipo_notificacion_id': notificacion.tipo_notificacion.id,
            'tipo_notificacion_nombre': notificacion.tipo_notificacion.nombre,
            'titulo': notificacion.titulo,
            'mensaje': notificacion.mensaje,
            'url_relacionada': notificacion.url_relacionada or '',
            'documento_id': notificacion.documento.id if notificacion.documento else None,
            'documento_titulo': notificacion.documento.get_titulo() if notificacion.documento and hasattr(notificacion.documento, 'get_titulo') else (notificacion.documento.titulo if notificacion.documento else None),
            'es_leida': notificacion.es_leida,
            'fecha_creacion': notificacion.fecha_creacion.isoformat() if notificacion.fecha_creacion else None,
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Notificación creada exitosamente',
            'data': notificacion_dict
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
            'error': f'Error al crear notificación: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def notificacion_detail(request, notificacion_id):
    """Obtiene los detalles de una notificación"""
    try:
        notificacion = get_object_or_404(
            Notificacion.objects.select_related('usuario', 'tipo_notificacion', 'documento'),
            id=notificacion_id
        )
        
        notificacion_dict = {
            'id': notificacion.id,
            'usuario_id': notificacion.usuario.id,
            'usuario_nombre': notificacion.usuario.get_full_name() or notificacion.usuario.username,
            'tipo_notificacion_id': notificacion.tipo_notificacion.id,
            'tipo_notificacion_nombre': notificacion.tipo_notificacion.nombre,
            'titulo': notificacion.titulo,
            'mensaje': notificacion.mensaje,
            'url_relacionada': notificacion.url_relacionada or '',
            'documento_id': notificacion.documento.id if notificacion.documento else None,
            'documento_titulo': notificacion.documento.get_titulo() if notificacion.documento and hasattr(notificacion.documento, 'get_titulo') else (notificacion.documento.titulo if notificacion.documento else None),
            'es_leida': notificacion.es_leida,
            'fecha_creacion': notificacion.fecha_creacion.isoformat() if notificacion.fecha_creacion else None,
        }
        
        return JsonResponse({
            'success': True,
            'data': notificacion_dict
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener notificación: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "PUT"])
def notificacion_update(request, notificacion_id):
    """Actualiza una notificación existente"""
    try:
        notificacion = get_object_or_404(Notificacion, id=notificacion_id)
        
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
        
        # Validar mensaje
        mensaje = data.get('mensaje', '').strip()
        if not mensaje:
            return JsonResponse({
                'success': False,
                'error': 'El mensaje es obligatorio'
            }, status=400)
        
        # Actualizar campos
        notificacion.titulo = titulo
        notificacion.mensaje = mensaje
        notificacion.url_relacionada = data.get('url_relacionada', '').strip() or None
        notificacion.es_leida = data.get('es_leida', notificacion.es_leida)
        
        # Actualizar usuario si se proporciona
        if 'usuario_id' in data and data['usuario_id']:
            usuario = get_object_or_404(User, id=data['usuario_id'])
            notificacion.usuario = usuario
        
        # Actualizar tipo de notificación si se proporciona
        if 'tipo_notificacion_id' in data and data['tipo_notificacion_id']:
            tipo_notificacion = get_object_or_404(TipoNotificacion, id=data['tipo_notificacion_id'])
            notificacion.tipo_notificacion = tipo_notificacion
        
        # Actualizar documento si se proporciona
        if 'documento_id' in data:
            if data['documento_id']:
                documento = get_object_or_404(Documento, id=data['documento_id'])
                notificacion.documento = documento
            else:
                notificacion.documento = None
        
        notificacion.full_clean()
        notificacion.save()
        
        # Retornar los datos actualizados
        notificacion_dict = {
            'id': notificacion.id,
            'usuario_id': notificacion.usuario.id,
            'usuario_nombre': notificacion.usuario.get_full_name() or notificacion.usuario.username,
            'tipo_notificacion_id': notificacion.tipo_notificacion.id,
            'tipo_notificacion_nombre': notificacion.tipo_notificacion.nombre,
            'titulo': notificacion.titulo,
            'mensaje': notificacion.mensaje,
            'url_relacionada': notificacion.url_relacionada or '',
            'documento_id': notificacion.documento.id if notificacion.documento else None,
            'documento_titulo': notificacion.documento.get_titulo() if notificacion.documento and hasattr(notificacion.documento, 'get_titulo') else (notificacion.documento.titulo if notificacion.documento else None),
            'es_leida': notificacion.es_leida,
            'fecha_creacion': notificacion.fecha_creacion.isoformat() if notificacion.fecha_creacion else None,
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Notificación actualizada exitosamente',
            'data': notificacion_dict
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
            'error': f'Error al actualizar notificación: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "DELETE"])
def notificacion_delete(request, notificacion_id):
    """Elimina una notificación"""
    try:
        notificacion = get_object_or_404(Notificacion, id=notificacion_id)
        
        # Manejar tanto POST con _method como DELETE directo
        if request.method == 'POST':
            data = json.loads(request.body) if request.body else {}
            if data.get('_method') != 'DELETE':
                return JsonResponse({
                    'success': False,
                    'error': 'Método no permitido'
                }, status=405)
        
        # Eliminar la notificación
        notificacion_titulo = notificacion.titulo[:50] + '...' if len(notificacion.titulo) > 50 else notificacion.titulo
        notificacion.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Notificación eliminada exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al eliminar notificación: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def notificacion_marcar_leida(request, notificacion_id):
    """Marca una notificación como leída"""
    try:
        notificacion = get_object_or_404(Notificacion, id=notificacion_id)
        notificacion.es_leida = True
        notificacion.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Notificación marcada como leída'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al marcar notificación como leída: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def notificacion_marcar_no_leida(request, notificacion_id):
    """Marca una notificación como no leída"""
    try:
        notificacion = get_object_or_404(Notificacion, id=notificacion_id)
        notificacion.es_leida = False
        notificacion.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Notificación marcada como no leída'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al marcar notificación como no leída: {str(e)}'
        }, status=500)
