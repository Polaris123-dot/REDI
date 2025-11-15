from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_datetime, parse_date
from datetime import datetime, date
import json
from .models import VisitaDocumento, DescargaArchivo, EstadisticaAgregada
from repositorio.models import Documento, Archivo
from django.contrib.auth.models import User


@login_required
@ensure_csrf_cookie
@require_http_methods(["GET"])
def index(request):
    """Vista principal de estadísticas"""
    # Verificar permisos
    if not (request.user.has_perm('estadisticas.view_visitadocumento') or 
            request.user.has_perm('estadisticas.view_descargaarchivo') or
            request.user.has_perm('estadisticas.view_estadisticaagregada') or
            request.user.is_superuser):
        messages.warning(request, 'No tienes permisos para acceder a estadísticas.')
        return redirect('usuarios:panel')
    return render(request, 'estadisticas/index.html')


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
def archivos_for_select(request):
    """Obtiene los archivos para usar en selects"""
    try:
        archivos = Archivo.objects.select_related('version', 'version__documento').all()
        archivos_data = []
        
        for archivo in archivos:
            documento = archivo.version.documento if archivo.version else None
            titulo = documento.get_titulo() if documento and hasattr(documento, 'get_titulo') else (documento.titulo if documento else f'Archivo #{archivo.id}')
            archivos_data.append({
                'id': archivo.id,
                'text': f"{titulo} - {archivo.nombre_archivo or 'Sin nombre'}",
                'nombre_archivo': archivo.nombre_archivo or '',
                'documento_id': documento.id if documento else None,
            })
        
        return JsonResponse({
            'success': True,
            'data': archivos_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener archivos: {str(e)}'
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
# VISTAS PARA VISITAS DE DOCUMENTOS
# ============================================================================

@login_required
@require_http_methods(["GET"])
def visitas_list(request):
    """Lista todas las visitas de documentos en formato JSON"""
    visitas = VisitaDocumento.objects.select_related('documento', 'usuario').all()
    visitas_data = []
    
    for visita in visitas:
        visita_dict = {
            'id': visita.id,
            'documento_id': visita.documento.id,
            'documento_titulo': visita.documento.get_titulo() if hasattr(visita.documento, 'get_titulo') else (visita.documento.titulo or f'Documento #{visita.documento.id}'),
            'usuario_id': visita.usuario.id if visita.usuario else None,
            'usuario_nombre': visita.usuario.get_full_name() if visita.usuario and visita.usuario.get_full_name() else (visita.usuario.username if visita.usuario else 'Anónimo'),
            'ip_address': str(visita.ip_address) if visita.ip_address else '',
            'user_agent': visita.user_agent or '',
            'pais': visita.pais or '',
            'ciudad': visita.ciudad or '',
            'referer': visita.referer or '',
            'tipo_acceso': visita.tipo_acceso,
            'tipo_acceso_display': visita.get_tipo_acceso_display(),
            'fecha': visita.fecha.isoformat() if visita.fecha else None,
        }
        visitas_data.append(visita_dict)
    
    return JsonResponse({
        'success': True,
        'data': visitas_data,
        'total': len(visitas_data)
    })


@login_required
@require_http_methods(["POST"])
def visita_create(request):
    """Crea una nueva visita de documento"""
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
        
        # Crear la visita
        visita = VisitaDocumento(
            documento=documento,
            usuario_id=data.get('usuario_id') or None,
            ip_address=data.get('ip_address') or None,
            user_agent=data.get('user_agent') or None,
            pais=data.get('pais') or None,
            ciudad=data.get('ciudad') or None,
            referer=data.get('referer') or None,
            tipo_acceso=data.get('tipo_acceso', 'vista'),
        )
        
        visita.full_clean()
        visita.save()
        
        # Retornar los datos de la visita creada
        visita_dict = {
            'id': visita.id,
            'documento_id': visita.documento.id,
            'documento_titulo': visita.documento.get_titulo() if hasattr(visita.documento, 'get_titulo') else (visita.documento.titulo or f'Documento #{visita.documento.id}'),
            'usuario_id': visita.usuario.id if visita.usuario else None,
            'usuario_nombre': visita.usuario.get_full_name() if visita.usuario and visita.usuario.get_full_name() else (visita.usuario.username if visita.usuario else 'Anónimo'),
            'ip_address': str(visita.ip_address) if visita.ip_address else '',
            'user_agent': visita.user_agent or '',
            'pais': visita.pais or '',
            'ciudad': visita.ciudad or '',
            'referer': visita.referer or '',
            'tipo_acceso': visita.tipo_acceso,
            'tipo_acceso_display': visita.get_tipo_acceso_display(),
            'fecha': visita.fecha.isoformat() if visita.fecha else None,
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Visita de documento creada exitosamente',
            'data': visita_dict
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
            'error': f'Error al crear visita de documento: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def visita_detail(request, visita_id):
    """Obtiene los detalles de una visita de documento"""
    try:
        visita = get_object_or_404(VisitaDocumento.objects.select_related('documento', 'usuario'), id=visita_id)
        
        visita_dict = {
            'id': visita.id,
            'documento_id': visita.documento.id,
            'documento_titulo': visita.documento.get_titulo() if hasattr(visita.documento, 'get_titulo') else (visita.documento.titulo or f'Documento #{visita.documento.id}'),
            'usuario_id': visita.usuario.id if visita.usuario else None,
            'usuario_nombre': visita.usuario.get_full_name() if visita.usuario and visita.usuario.get_full_name() else (visita.usuario.username if visita.usuario else 'Anónimo'),
            'ip_address': str(visita.ip_address) if visita.ip_address else '',
            'user_agent': visita.user_agent or '',
            'pais': visita.pais or '',
            'ciudad': visita.ciudad or '',
            'referer': visita.referer or '',
            'tipo_acceso': visita.tipo_acceso,
            'tipo_acceso_display': visita.get_tipo_acceso_display(),
            'fecha': visita.fecha.isoformat() if visita.fecha else None,
        }
        
        return JsonResponse({
            'success': True,
            'data': visita_dict
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener visita de documento: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "PUT"])
def visita_update(request, visita_id):
    """Actualiza una visita de documento existente"""
    try:
        visita = get_object_or_404(VisitaDocumento, id=visita_id)
        
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
        
        # Actualizar campos
        if 'documento_id' in data:
            documento = get_object_or_404(Documento, id=data.get('documento_id'))
            visita.documento = documento
        
        visita.usuario_id = data.get('usuario_id') or None
        visita.ip_address = data.get('ip_address') or None
        visita.user_agent = data.get('user_agent') or None
        visita.pais = data.get('pais') or None
        visita.ciudad = data.get('ciudad') or None
        visita.referer = data.get('referer') or None
        if 'tipo_acceso' in data:
            visita.tipo_acceso = data.get('tipo_acceso')
        
        visita.full_clean()
        visita.save()
        
        # Retornar los datos actualizados
        visita_dict = {
            'id': visita.id,
            'documento_id': visita.documento.id,
            'documento_titulo': visita.documento.get_titulo() if hasattr(visita.documento, 'get_titulo') else (visita.documento.titulo or f'Documento #{visita.documento.id}'),
            'usuario_id': visita.usuario.id if visita.usuario else None,
            'usuario_nombre': visita.usuario.get_full_name() if visita.usuario and visita.usuario.get_full_name() else (visita.usuario.username if visita.usuario else 'Anónimo'),
            'ip_address': str(visita.ip_address) if visita.ip_address else '',
            'user_agent': visita.user_agent or '',
            'pais': visita.pais or '',
            'ciudad': visita.ciudad or '',
            'referer': visita.referer or '',
            'tipo_acceso': visita.tipo_acceso,
            'tipo_acceso_display': visita.get_tipo_acceso_display(),
            'fecha': visita.fecha.isoformat() if visita.fecha else None,
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Visita de documento actualizada exitosamente',
            'data': visita_dict
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
            'error': f'Error al actualizar visita de documento: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "DELETE"])
def visita_delete(request, visita_id):
    """Elimina una visita de documento"""
    try:
        visita = get_object_or_404(VisitaDocumento, id=visita_id)
        
        # Manejar tanto POST con _method como DELETE directo
        if request.method == 'POST':
            data = json.loads(request.body) if request.body else {}
            if data.get('_method') != 'DELETE':
                return JsonResponse({
                    'success': False,
                    'error': 'Método no permitido'
                }, status=405)
        
        # Eliminar la visita
        visita.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Visita de documento eliminada exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al eliminar visita de documento: {str(e)}'
        }, status=500)


# ============================================================================
# VISTAS PARA DESCARGAS DE ARCHIVOS
# ============================================================================

@login_required
@require_http_methods(["GET"])
def descargas_list(request):
    """Lista todas las descargas de archivos en formato JSON"""
    descargas = DescargaArchivo.objects.select_related('archivo', 'archivo__version', 'archivo__version__documento', 'usuario').all()
    descargas_data = []
    
    for descarga in descargas:
        documento = descarga.archivo.version.documento if descarga.archivo.version else None
        documento_titulo = documento.get_titulo() if documento and hasattr(documento, 'get_titulo') else (documento.titulo if documento else 'Sin documento')
        
        descarga_dict = {
            'id': descarga.id,
            'archivo_id': descarga.archivo.id,
            'archivo_nombre': descarga.archivo.nombre_archivo or '',
            'documento_id': documento.id if documento else None,
            'documento_titulo': documento_titulo,
            'usuario_id': descarga.usuario.id if descarga.usuario else None,
            'usuario_nombre': descarga.usuario.get_full_name() if descarga.usuario and descarga.usuario.get_full_name() else (descarga.usuario.username if descarga.usuario else 'Anónimo'),
            'ip_address': str(descarga.ip_address) if descarga.ip_address else '',
            'fecha': descarga.fecha.isoformat() if descarga.fecha else None,
        }
        descargas_data.append(descarga_dict)
    
    return JsonResponse({
        'success': True,
        'data': descargas_data,
        'total': len(descargas_data)
    })


@login_required
@require_http_methods(["POST"])
def descarga_create(request):
    """Crea una nueva descarga de archivo"""
    try:
        data = json.loads(request.body)
        
        # Validar campos requeridos
        archivo_id = data.get('archivo_id')
        if not archivo_id:
            return JsonResponse({
                'success': False,
                'error': 'El archivo es obligatorio'
            }, status=400)
        
        archivo = get_object_or_404(Archivo, id=archivo_id)
        
        # Crear la descarga
        descarga = DescargaArchivo(
            archivo=archivo,
            usuario_id=data.get('usuario_id') or None,
            ip_address=data.get('ip_address') or None,
        )
        
        descarga.full_clean()
        descarga.save()
        
        # Retornar los datos de la descarga creada
        documento = descarga.archivo.version.documento if descarga.archivo.version else None
        documento_titulo = documento.get_titulo() if documento and hasattr(documento, 'get_titulo') else (documento.titulo if documento else 'Sin documento')
        
        descarga_dict = {
            'id': descarga.id,
            'archivo_id': descarga.archivo.id,
            'archivo_nombre': descarga.archivo.nombre_archivo or '',
            'documento_id': documento.id if documento else None,
            'documento_titulo': documento_titulo,
            'usuario_id': descarga.usuario.id if descarga.usuario else None,
            'usuario_nombre': descarga.usuario.get_full_name() if descarga.usuario and descarga.usuario.get_full_name() else (descarga.usuario.username if descarga.usuario else 'Anónimo'),
            'ip_address': str(descarga.ip_address) if descarga.ip_address else '',
            'fecha': descarga.fecha.isoformat() if descarga.fecha else None,
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Descarga de archivo creada exitosamente',
            'data': descarga_dict
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
            'error': f'Error al crear descarga de archivo: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def descarga_detail(request, descarga_id):
    """Obtiene los detalles de una descarga de archivo"""
    try:
        descarga = get_object_or_404(DescargaArchivo.objects.select_related('archivo', 'archivo__version', 'archivo__version__documento', 'usuario'), id=descarga_id)
        
        documento = descarga.archivo.version.documento if descarga.archivo.version else None
        documento_titulo = documento.get_titulo() if documento and hasattr(documento, 'get_titulo') else (documento.titulo if documento else 'Sin documento')
        
        descarga_dict = {
            'id': descarga.id,
            'archivo_id': descarga.archivo.id,
            'archivo_nombre': descarga.archivo.nombre_archivo or '',
            'documento_id': documento.id if documento else None,
            'documento_titulo': documento_titulo,
            'usuario_id': descarga.usuario.id if descarga.usuario else None,
            'usuario_nombre': descarga.usuario.get_full_name() if descarga.usuario and descarga.usuario.get_full_name() else (descarga.usuario.username if descarga.usuario else 'Anónimo'),
            'ip_address': str(descarga.ip_address) if descarga.ip_address else '',
            'fecha': descarga.fecha.isoformat() if descarga.fecha else None,
        }
        
        return JsonResponse({
            'success': True,
            'data': descarga_dict
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener descarga de archivo: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "PUT"])
def descarga_update(request, descarga_id):
    """Actualiza una descarga de archivo existente"""
    try:
        descarga = get_object_or_404(DescargaArchivo, id=descarga_id)
        
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
        
        # Actualizar campos
        if 'archivo_id' in data:
            archivo = get_object_or_404(Archivo, id=data.get('archivo_id'))
            descarga.archivo = archivo
        
        descarga.usuario_id = data.get('usuario_id') or None
        descarga.ip_address = data.get('ip_address') or None
        
        descarga.full_clean()
        descarga.save()
        
        # Retornar los datos actualizados
        documento = descarga.archivo.version.documento if descarga.archivo.version else None
        documento_titulo = documento.get_titulo() if documento and hasattr(documento, 'get_titulo') else (documento.titulo if documento else 'Sin documento')
        
        descarga_dict = {
            'id': descarga.id,
            'archivo_id': descarga.archivo.id,
            'archivo_nombre': descarga.archivo.nombre_archivo or '',
            'documento_id': documento.id if documento else None,
            'documento_titulo': documento_titulo,
            'usuario_id': descarga.usuario.id if descarga.usuario else None,
            'usuario_nombre': descarga.usuario.get_full_name() if descarga.usuario and descarga.usuario.get_full_name() else (descarga.usuario.username if descarga.usuario else 'Anónimo'),
            'ip_address': str(descarga.ip_address) if descarga.ip_address else '',
            'fecha': descarga.fecha.isoformat() if descarga.fecha else None,
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Descarga de archivo actualizada exitosamente',
            'data': descarga_dict
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
            'error': f'Error al actualizar descarga de archivo: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "DELETE"])
def descarga_delete(request, descarga_id):
    """Elimina una descarga de archivo"""
    try:
        descarga = get_object_or_404(DescargaArchivo, id=descarga_id)
        
        # Manejar tanto POST con _method como DELETE directo
        if request.method == 'POST':
            data = json.loads(request.body) if request.body else {}
            if data.get('_method') != 'DELETE':
                return JsonResponse({
                    'success': False,
                    'error': 'Método no permitido'
                }, status=405)
        
        # Eliminar la descarga
        descarga.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Descarga de archivo eliminada exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al eliminar descarga de archivo: {str(e)}'
        }, status=500)


# ============================================================================
# VISTAS PARA ESTADÍSTICAS AGREGADAS
# ============================================================================

@login_required
@require_http_methods(["GET"])
def estadisticas_agregadas_list(request):
    """Lista todas las estadísticas agregadas en formato JSON"""
    estadisticas = EstadisticaAgregada.objects.select_related('documento').all()
    estadisticas_data = []
    
    for estadistica in estadisticas:
        estadistica_dict = {
            'id': estadistica.id,
            'documento_id': estadistica.documento.id,
            'documento_titulo': estadistica.documento.get_titulo() if hasattr(estadistica.documento, 'get_titulo') else (estadistica.documento.titulo or f'Documento #{estadistica.documento.id}'),
            'periodo': estadistica.periodo,
            'periodo_display': estadistica.get_periodo_display(),
            'fecha_inicio': estadistica.fecha_inicio.isoformat() if estadistica.fecha_inicio else None,
            'total_visitas': estadistica.total_visitas,
            'total_descargas': estadistica.total_descargas,
            'visitas_unicas': estadistica.visitas_unicas,
            'descargas_unicas': estadistica.descargas_unicas,
            'tiempo_promedio_lectura': estadistica.tiempo_promedio_lectura,
        }
        estadisticas_data.append(estadistica_dict)
    
    return JsonResponse({
        'success': True,
        'data': estadisticas_data,
        'total': len(estadisticas_data)
    })


@login_required
@require_http_methods(["POST"])
def estadistica_agregada_create(request):
    """Crea una nueva estadística agregada"""
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
        
        periodo = data.get('periodo')
        if not periodo:
            return JsonResponse({
                'success': False,
                'error': 'El período es obligatorio'
            }, status=400)
        
        fecha_inicio = data.get('fecha_inicio')
        if not fecha_inicio:
            return JsonResponse({
                'success': False,
                'error': 'La fecha de inicio es obligatoria'
            }, status=400)
        
        # Parsear fecha
        try:
            fecha_inicio_obj = parse_date(fecha_inicio)
            if not fecha_inicio_obj:
                return JsonResponse({
                    'success': False,
                    'error': 'La fecha de inicio debe ser una fecha válida (formato: YYYY-MM-DD)'
                }, status=400)
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'error': 'La fecha de inicio debe ser una fecha válida (formato: YYYY-MM-DD)'
            }, status=400)
        
        # Verificar que no exista una estadística con los mismos valores
        if EstadisticaAgregada.objects.filter(documento=documento, periodo=periodo, fecha_inicio=fecha_inicio_obj).exists():
            return JsonResponse({
                'success': False,
                'error': 'Ya existe una estadística agregada para este documento, período y fecha de inicio'
            }, status=400)
        
        # Crear la estadística
        estadistica = EstadisticaAgregada(
            documento=documento,
            periodo=periodo,
            fecha_inicio=fecha_inicio_obj,
            total_visitas=data.get('total_visitas', 0),
            total_descargas=data.get('total_descargas', 0),
            visitas_unicas=data.get('visitas_unicas', 0),
            descargas_unicas=data.get('descargas_unicas', 0),
            tiempo_promedio_lectura=data.get('tiempo_promedio_lectura') or None,
        )
        
        estadistica.full_clean()
        estadistica.save()
        
        # Retornar los datos de la estadística creada
        estadistica_dict = {
            'id': estadistica.id,
            'documento_id': estadistica.documento.id,
            'documento_titulo': estadistica.documento.get_titulo() if hasattr(estadistica.documento, 'get_titulo') else (estadistica.documento.titulo or f'Documento #{estadistica.documento.id}'),
            'periodo': estadistica.periodo,
            'periodo_display': estadistica.get_periodo_display(),
            'fecha_inicio': estadistica.fecha_inicio.isoformat() if estadistica.fecha_inicio else None,
            'total_visitas': estadistica.total_visitas,
            'total_descargas': estadistica.total_descargas,
            'visitas_unicas': estadistica.visitas_unicas,
            'descargas_unicas': estadistica.descargas_unicas,
            'tiempo_promedio_lectura': estadistica.tiempo_promedio_lectura,
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Estadística agregada creada exitosamente',
            'data': estadistica_dict
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
            'error': f'Error al crear estadística agregada: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def estadistica_agregada_detail(request, estadistica_id):
    """Obtiene los detalles de una estadística agregada"""
    try:
        estadistica = get_object_or_404(EstadisticaAgregada.objects.select_related('documento'), id=estadistica_id)
        
        estadistica_dict = {
            'id': estadistica.id,
            'documento_id': estadistica.documento.id,
            'documento_titulo': estadistica.documento.get_titulo() if hasattr(estadistica.documento, 'get_titulo') else (estadistica.documento.titulo or f'Documento #{estadistica.documento.id}'),
            'periodo': estadistica.periodo,
            'periodo_display': estadistica.get_periodo_display(),
            'fecha_inicio': estadistica.fecha_inicio.isoformat() if estadistica.fecha_inicio else None,
            'total_visitas': estadistica.total_visitas,
            'total_descargas': estadistica.total_descargas,
            'visitas_unicas': estadistica.visitas_unicas,
            'descargas_unicas': estadistica.descargas_unicas,
            'tiempo_promedio_lectura': estadistica.tiempo_promedio_lectura,
        }
        
        return JsonResponse({
            'success': True,
            'data': estadistica_dict
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener estadística agregada: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "PUT"])
def estadistica_agregada_update(request, estadistica_id):
    """Actualiza una estadística agregada existente"""
    try:
        estadistica = get_object_or_404(EstadisticaAgregada, id=estadistica_id)
        
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
        
        # Actualizar campos
        if 'documento_id' in data:
            documento = get_object_or_404(Documento, id=data.get('documento_id'))
            estadistica.documento = documento
        
        if 'periodo' in data:
            estadistica.periodo = data.get('periodo')
        
        if 'fecha_inicio' in data:
            fecha_inicio = data.get('fecha_inicio')
            try:
                fecha_inicio_obj = parse_date(fecha_inicio)
                if not fecha_inicio_obj:
                    return JsonResponse({
                        'success': False,
                        'error': 'La fecha de inicio debe ser una fecha válida (formato: YYYY-MM-DD)'
                    }, status=400)
                estadistica.fecha_inicio = fecha_inicio_obj
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': 'La fecha de inicio debe ser una fecha válida (formato: YYYY-MM-DD)'
                }, status=400)
        
        # Verificar que no exista otra estadística con los mismos valores
        if 'documento_id' in data or 'periodo' in data or 'fecha_inicio' in data:
            documento_check = estadistica.documento
            periodo_check = estadistica.periodo
            fecha_inicio_check = estadistica.fecha_inicio
            
            if EstadisticaAgregada.objects.filter(documento=documento_check, periodo=periodo_check, fecha_inicio=fecha_inicio_check).exclude(id=estadistica_id).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Ya existe otra estadística agregada para este documento, período y fecha de inicio'
                }, status=400)
        
        if 'total_visitas' in data:
            estadistica.total_visitas = data.get('total_visitas', 0)
        if 'total_descargas' in data:
            estadistica.total_descargas = data.get('total_descargas', 0)
        if 'visitas_unicas' in data:
            estadistica.visitas_unicas = data.get('visitas_unicas', 0)
        if 'descargas_unicas' in data:
            estadistica.descargas_unicas = data.get('descargas_unicas', 0)
        if 'tiempo_promedio_lectura' in data:
            estadistica.tiempo_promedio_lectura = data.get('tiempo_promedio_lectura') or None
        
        estadistica.full_clean()
        estadistica.save()
        
        # Retornar los datos actualizados
        estadistica_dict = {
            'id': estadistica.id,
            'documento_id': estadistica.documento.id,
            'documento_titulo': estadistica.documento.get_titulo() if hasattr(estadistica.documento, 'get_titulo') else (estadistica.documento.titulo or f'Documento #{estadistica.documento.id}'),
            'periodo': estadistica.periodo,
            'periodo_display': estadistica.get_periodo_display(),
            'fecha_inicio': estadistica.fecha_inicio.isoformat() if estadistica.fecha_inicio else None,
            'total_visitas': estadistica.total_visitas,
            'total_descargas': estadistica.total_descargas,
            'visitas_unicas': estadistica.visitas_unicas,
            'descargas_unicas': estadistica.descargas_unicas,
            'tiempo_promedio_lectura': estadistica.tiempo_promedio_lectura,
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Estadística agregada actualizada exitosamente',
            'data': estadistica_dict
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
            'error': f'Error al actualizar estadística agregada: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "DELETE"])
def estadistica_agregada_delete(request, estadistica_id):
    """Elimina una estadística agregada"""
    try:
        estadistica = get_object_or_404(EstadisticaAgregada, id=estadistica_id)
        
        # Manejar tanto POST con _method como DELETE directo
        if request.method == 'POST':
            data = json.loads(request.body) if request.body else {}
            if data.get('_method') != 'DELETE':
                return JsonResponse({
                    'success': False,
                    'error': 'Método no permitido'
                }, status=405)
        
        # Eliminar la estadística
        estadistica.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Estadística agregada eliminada exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al eliminar estadística agregada: {str(e)}'
        }, status=500)
