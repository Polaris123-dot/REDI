from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.db.models import Q
from datetime import datetime, timedelta
import json
from .models import ConfiguracionSistema, LogSistema


@login_required
@ensure_csrf_cookie
@require_http_methods(["GET"])
def index(request):
    """Vista principal de configuración"""
    # Verificar permisos (solo superusuarios o usuarios con permisos específicos)
    if not (request.user.has_perm('configuracion.view_configuracionsistema') or 
            request.user.has_perm('configuracion.view_logsistema') or
            request.user.is_superuser):
        messages.warning(request, 'No tienes permisos para acceder a configuración.')
        return redirect('usuarios:panel')
    return render(request, 'configuracion/index.html')


# ============================================================================
# VISTAS PARA CONFIGURACIÓN DEL SISTEMA
# ============================================================================

@login_required
@require_http_methods(["GET"])
def configuraciones_list(request):
    """Lista todas las configuraciones en formato JSON"""
    configuraciones = ConfiguracionSistema.objects.all().order_by('categoria', 'clave')
    configuraciones_data = []
    
    for config in configuraciones:
        config_dict = {
            'id': config.id,
            'clave': config.clave,
            'valor': config.valor or '',
            'tipo': config.tipo,
            'tipo_display': config.get_tipo_display(),
            'categoria': config.categoria or '',
            'descripcion': config.descripcion or '',
            'es_editable': config.es_editable,
        }
        configuraciones_data.append(config_dict)
    
    return JsonResponse({
        'success': True,
        'data': configuraciones_data,
        'total': len(configuraciones_data)
    })


@login_required
@require_http_methods(["POST"])
def configuracion_create(request):
    """Crea una nueva configuración"""
    try:
        data = json.loads(request.body)
        
        # Validar campos requeridos
        clave = data.get('clave', '').strip()
        if not clave:
            return JsonResponse({
                'success': False,
                'error': 'La clave es obligatoria'
            }, status=400)
        
        # Verificar que la clave no exista
        if ConfiguracionSistema.objects.filter(clave=clave).exists():
            return JsonResponse({
                'success': False,
                'error': 'Ya existe una configuración con esta clave'
            }, status=400)
        
        # Validar valor según tipo
        tipo = data.get('tipo', 'texto')
        valor = data.get('valor', '').strip()
        
        # Crear la configuración
        configuracion = ConfiguracionSistema(
            clave=clave,
            valor=valor or None,
            tipo=tipo,
            categoria=data.get('categoria', '').strip() or None,
            descripcion=data.get('descripcion', '').strip() or None,
            es_editable=data.get('es_editable', True),
        )
        
        configuracion.full_clean()
        configuracion.save()
        
        # Retornar los datos de la configuración creada
        config_dict = {
            'id': configuracion.id,
            'clave': configuracion.clave,
            'valor': configuracion.valor or '',
            'tipo': configuracion.tipo,
            'tipo_display': configuracion.get_tipo_display(),
            'categoria': configuracion.categoria or '',
            'descripcion': configuracion.descripcion or '',
            'es_editable': configuracion.es_editable,
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Configuración creada exitosamente',
            'data': config_dict
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
            'error': f'Error al crear configuración: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def configuracion_detail(request, configuracion_id):
    """Obtiene los detalles de una configuración"""
    try:
        configuracion = get_object_or_404(ConfiguracionSistema, id=configuracion_id)
        
        config_dict = {
            'id': configuracion.id,
            'clave': configuracion.clave,
            'valor': configuracion.valor or '',
            'tipo': configuracion.tipo,
            'tipo_display': configuracion.get_tipo_display(),
            'categoria': configuracion.categoria or '',
            'descripcion': configuracion.descripcion or '',
            'es_editable': configuracion.es_editable,
        }
        
        return JsonResponse({
            'success': True,
            'data': config_dict
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener configuración: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "PUT"])
def configuracion_update(request, configuracion_id):
    """Actualiza una configuración existente"""
    try:
        configuracion = get_object_or_404(ConfiguracionSistema, id=configuracion_id)
        
        # Verificar si es editable
        if not configuracion.es_editable:
            return JsonResponse({
                'success': False,
                'error': 'Esta configuración no es editable'
            }, status=400)
        
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
        
        # Validar clave
        clave = data.get('clave', '').strip()
        if not clave:
            return JsonResponse({
                'success': False,
                'error': 'La clave es obligatoria'
            }, status=400)
        
        # Verificar que la clave no exista en otra configuración
        if ConfiguracionSistema.objects.filter(clave=clave).exclude(id=configuracion_id).exists():
            return JsonResponse({
                'success': False,
                'error': 'Ya existe otra configuración con esta clave'
            }, status=400)
        
        # Actualizar campos
        configuracion.clave = clave
        configuracion.valor = data.get('valor', '').strip() or None
        configuracion.tipo = data.get('tipo', configuracion.tipo)
        configuracion.categoria = data.get('categoria', '').strip() or None
        configuracion.descripcion = data.get('descripcion', '').strip() or None
        configuracion.es_editable = data.get('es_editable', configuracion.es_editable)
        
        configuracion.full_clean()
        configuracion.save()
        
        # Retornar los datos actualizados
        config_dict = {
            'id': configuracion.id,
            'clave': configuracion.clave,
            'valor': configuracion.valor or '',
            'tipo': configuracion.tipo,
            'tipo_display': configuracion.get_tipo_display(),
            'categoria': configuracion.categoria or '',
            'descripcion': configuracion.descripcion or '',
            'es_editable': configuracion.es_editable,
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Configuración actualizada exitosamente',
            'data': config_dict
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
            'error': f'Error al actualizar configuración: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "DELETE"])
def configuracion_delete(request, configuracion_id):
    """Elimina una configuración"""
    try:
        configuracion = get_object_or_404(ConfiguracionSistema, id=configuracion_id)
        
        # Manejar tanto POST con _method como DELETE directo
        if request.method == 'POST':
            data = json.loads(request.body) if request.body else {}
            if data.get('_method') != 'DELETE':
                return JsonResponse({
                    'success': False,
                    'error': 'Método no permitido'
                }, status=405)
        
        # Verificar si es editable (solo se pueden eliminar configuraciones editables)
        if not configuracion.es_editable:
            return JsonResponse({
                'success': False,
                'error': 'No se puede eliminar una configuración que no es editable'
            }, status=400)
        
        # Eliminar la configuración
        config_clave = configuracion.clave
        configuracion.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Configuración "{config_clave}" eliminada exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al eliminar configuración: {str(e)}'
        }, status=500)


# ============================================================================
# VISTAS PARA LOGS DEL SISTEMA
# ============================================================================

@login_required
@require_http_methods(["GET"])
def logs_list(request):
    """Lista todos los logs en formato JSON"""
    # Filtros opcionales
    nivel = request.GET.get('nivel', '')
    modulo = request.GET.get('modulo', '')
    usuario_id = request.GET.get('usuario_id', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    limit = request.GET.get('limit', '1000')  # Límite por defecto
    
    try:
        limit = int(limit)
        if limit > 10000:  # Límite máximo
            limit = 10000
    except (ValueError, TypeError):
        limit = 1000
    
    # Consulta base
    logs = LogSistema.objects.select_related('usuario').all()
    
    # Aplicar filtros
    if nivel:
        logs = logs.filter(nivel=nivel)
    if modulo:
        logs = logs.filter(modulo__icontains=modulo)
    if usuario_id:
        logs = logs.filter(usuario_id=usuario_id)
    if fecha_desde:
        try:
            fecha_desde_obj = datetime.fromisoformat(fecha_desde.replace('Z', '+00:00'))
            logs = logs.filter(fecha__gte=fecha_desde_obj)
        except (ValueError, AttributeError):
            pass
    if fecha_hasta:
        try:
            fecha_hasta_obj = datetime.fromisoformat(fecha_hasta.replace('Z', '+00:00'))
            logs = logs.filter(fecha__lte=fecha_hasta_obj)
        except (ValueError, AttributeError):
            pass
    
    # Ordenar y aplicar límite después de los filtros
    logs = logs.order_by('-fecha')[:limit]
    
    logs_data = []
    
    for log in logs:
        log_dict = {
            'id': log.id,
            'nivel': log.nivel,
            'nivel_display': log.get_nivel_display(),
            'modulo': log.modulo or '',
            'mensaje': log.mensaje,
            'usuario_id': log.usuario.id if log.usuario else None,
            'usuario_nombre': log.usuario.get_full_name() or log.usuario.username if log.usuario else None,
            'ip_address': str(log.ip_address) if log.ip_address else '',
            'datos_adicionales': log.datos_adicionales if log.datos_adicionales else None,
            'fecha': log.fecha.isoformat() if log.fecha else None,
        }
        logs_data.append(log_dict)
    
    return JsonResponse({
        'success': True,
        'data': logs_data,
        'total': len(logs_data)
    })


@login_required
@require_http_methods(["GET"])
def log_detail(request, log_id):
    """Obtiene los detalles de un log"""
    try:
        log = get_object_or_404(LogSistema.objects.select_related('usuario'), id=log_id)
        
        log_dict = {
            'id': log.id,
            'nivel': log.nivel,
            'nivel_display': log.get_nivel_display(),
            'modulo': log.modulo or '',
            'mensaje': log.mensaje,
            'usuario_id': log.usuario.id if log.usuario else None,
            'usuario_nombre': log.usuario.get_full_name() or log.usuario.username if log.usuario else None,
            'ip_address': str(log.ip_address) if log.ip_address else '',
            'datos_adicionales': log.datos_adicionales if log.datos_adicionales else None,
            'fecha': log.fecha.isoformat() if log.fecha else None,
        }
        
        return JsonResponse({
            'success': True,
            'data': log_dict
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener log: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "DELETE"])
def log_delete(request, log_id):
    """Elimina un log"""
    try:
        # Solo superusuarios pueden eliminar logs
        if not request.user.is_superuser:
            return JsonResponse({
                'success': False,
                'error': 'Solo los superusuarios pueden eliminar logs'
            }, status=403)
        
        log = get_object_or_404(LogSistema, id=log_id)
        
        # Manejar tanto POST con _method como DELETE directo
        if request.method == 'POST':
            data = json.loads(request.body) if request.body else {}
            if data.get('_method') != 'DELETE':
                return JsonResponse({
                    'success': False,
                    'error': 'Método no permitido'
                }, status=405)
        
        # Eliminar el log
        log.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Log eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al eliminar log: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def logs_limpiar(request):
    """Limpia los logs según criterios"""
    try:
        # Solo superusuarios pueden limpiar logs
        if not request.user.is_superuser:
            return JsonResponse({
                'success': False,
                'error': 'Solo los superusuarios pueden limpiar logs'
            }, status=403)
        
        data = json.loads(request.body) if request.body else {}
        
        # Criterios de limpieza
        nivel = data.get('nivel', '')
        dias = data.get('dias', None)
        nivel_minimo = data.get('nivel_minimo', '')  # Eliminar logs de nivel menor o igual
        
        # Construir consulta
        logs = LogSistema.objects.all()
        
        if nivel:
            logs = logs.filter(nivel=nivel)
        
        if nivel_minimo:
            # Mapear niveles a números para comparar
            niveles = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            try:
                nivel_index = niveles.index(nivel_minimo)
                niveles_a_eliminar = niveles[:nivel_index + 1]
                logs = logs.filter(nivel__in=niveles_a_eliminar)
            except ValueError:
                pass
        
        if dias:
            try:
                dias_int = int(dias)
                fecha_limite = datetime.now() - timedelta(days=dias_int)
                logs = logs.filter(fecha__lt=fecha_limite)
            except (ValueError, TypeError):
                pass
        
        # Contar logs a eliminar
        count = logs.count()
        
        # Eliminar logs
        logs.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'{count} log(s) eliminado(s) exitosamente'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'JSON inválido'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al limpiar logs: {str(e)}'
        }, status=500)
