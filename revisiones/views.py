from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from datetime import datetime
import json
from .models import CriterioRevision, ProcesoRevision, Revision, EvaluacionCriterio
from repositorio.models import Documento
from django.contrib.auth.models import User


@login_required
@ensure_csrf_cookie
@require_http_methods(["GET"])
def index(request):
    """Vista principal de revisiones"""
    # Verificar permisos
    if not (request.user.has_perm('revisiones.view_criteriorevision') or 
            request.user.has_perm('revisiones.view_procesorevision') or
            request.user.has_perm('revisiones.view_revision') or
            request.user.has_perm('revisiones.view_evaluacioncriterio') or
            request.user.is_superuser):
        messages.warning(request, 'No tienes permisos para acceder a revisiones.')
        return redirect('usuarios:panel')
    return render(request, 'revisiones/index.html')


# ============================================================================
# VISTAS AUXILIARES PARA SELECTS
# ============================================================================

@login_required
@require_http_methods(["GET"])
def criterios_for_select(request):
    """Obtiene los criterios de revisión para usar en selects"""
    try:
        criterios = CriterioRevision.objects.all().order_by('nombre')
        criterios_data = []
        
        for criterio in criterios:
            criterios_data.append({
                'id': criterio.id,
                'text': criterio.nombre,
                'tipo': criterio.tipo,
                'escala_minima': criterio.escala_minima,
                'escala_maxima': criterio.escala_maxima,
                'opciones': criterio.opciones or [],
                'es_obligatorio': criterio.es_obligatorio,
            })
        
        return JsonResponse({
            'success': True,
            'data': criterios_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener criterios: {str(e)}'
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
def procesos_for_select(request):
    """Obtiene los procesos de revisión para usar en selects"""
    try:
        procesos = ProcesoRevision.objects.select_related('documento', 'iniciado_por').all()
        procesos_data = []
        
        for proceso in procesos:
            documento_titulo = proceso.documento.get_titulo() if hasattr(proceso.documento, 'get_titulo') else (proceso.documento.titulo or f'Documento #{proceso.documento.id}')
            procesos_data.append({
                'id': proceso.id,
                'text': f"{documento_titulo} - {proceso.get_tipo_revision_display()} ({proceso.get_estado_display()})",
                'documento_id': proceso.documento.id,
                'documento_titulo': documento_titulo,
                'tipo_revision': proceso.tipo_revision,
                'estado': proceso.estado,
            })
        
        return JsonResponse({
            'success': True,
            'data': procesos_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener procesos: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def revisiones_for_select(request):
    """Obtiene las revisiones para usar en selects"""
    try:
        proceso_id = request.GET.get('proceso_id', None)
        if proceso_id:
            revisiones = Revision.objects.select_related('proceso_revision', 'revisor').filter(proceso_revision_id=proceso_id)
        else:
            revisiones = Revision.objects.select_related('proceso_revision', 'revisor').all()
        
        revisiones_data = []
        
        for revision in revisiones:
            revisor_nombre = revision.revisor.get_full_name() or revision.revisor.username
            proceso_texto = f"{revision.proceso_revision.documento.get_titulo() if hasattr(revision.proceso_revision.documento, 'get_titulo') else (revision.proceso_revision.documento.titulo or f'Doc #{revision.proceso_revision.documento.id}')} - {revision.proceso_revision.get_tipo_revision_display()}"
            revisiones_data.append({
                'id': revision.id,
                'text': f"{proceso_texto} - {revisor_nombre} ({revision.get_estado_display()})",
                'proceso_revision_id': revision.proceso_revision.id,
                'revisor_id': revision.revisor.id,
                'revisor_nombre': revisor_nombre,
                'estado': revision.estado,
            })
        
        return JsonResponse({
            'success': True,
            'data': revisiones_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener revisiones: {str(e)}'
        }, status=500)


# ============================================================================
# VISTAS PARA CRITERIOS DE REVISIÓN
# ============================================================================

@login_required
@require_http_methods(["GET"])
def criterios_list(request):
    """Lista todos los criterios de revisión en formato JSON"""
    criterios = CriterioRevision.objects.all()
    criterios_data = []
    
    for criterio in criterios:
        criterio_dict = {
            'id': criterio.id,
            'nombre': criterio.nombre,
            'descripcion': criterio.descripcion or '',
            'tipo': criterio.tipo,
            'tipo_display': criterio.get_tipo_display(),
            'escala_minima': criterio.escala_minima,
            'escala_maxima': criterio.escala_maxima,
            'opciones': criterio.opciones or [],
            'es_obligatorio': criterio.es_obligatorio,
        }
        criterios_data.append(criterio_dict)
    
    return JsonResponse({
        'success': True,
        'data': criterios_data,
        'total': len(criterios_data)
    })


@login_required
@require_http_methods(["POST"])
def criterio_create(request):
    """Crea un nuevo criterio de revisión"""
    try:
        data = json.loads(request.body)
        
        # Validar campos requeridos
        nombre = data.get('nombre', '').strip()
        if not nombre:
            return JsonResponse({
                'success': False,
                'error': 'El nombre es obligatorio'
            }, status=400)
        
        tipo = data.get('tipo', 'numerico')
        escala_minima = data.get('escala_minima')
        escala_maxima = data.get('escala_maxima')
        opciones = data.get('opciones')
        
        # Validar según el tipo
        if tipo == 'numerico':
            if escala_minima is None or escala_maxima is None:
                return JsonResponse({
                    'success': False,
                    'error': 'La escala mínima y máxima son obligatorias para criterios numéricos'
                }, status=400)
            if escala_minima >= escala_maxima:
                return JsonResponse({
                    'success': False,
                    'error': 'La escala mínima debe ser menor que la máxima'
                }, status=400)
        elif tipo == 'opcion':
            if not opciones or not isinstance(opciones, list) or len(opciones) == 0:
                return JsonResponse({
                    'success': False,
                    'error': 'Las opciones son obligatorias para criterios de tipo opción'
                }, status=400)
        
        # Crear el criterio
        criterio = CriterioRevision(
            nombre=nombre,
            descripcion=data.get('descripcion', '').strip() or None,
            tipo=tipo,
            escala_minima=escala_minima,
            escala_maxima=escala_maxima,
            opciones=opciones if tipo == 'opcion' else None,
            es_obligatorio=data.get('es_obligatorio', False),
        )
        
        criterio.full_clean()
        criterio.save()
        
        # Retornar los datos del criterio creado
        criterio_dict = {
            'id': criterio.id,
            'nombre': criterio.nombre,
            'descripcion': criterio.descripcion or '',
            'tipo': criterio.tipo,
            'tipo_display': criterio.get_tipo_display(),
            'escala_minima': criterio.escala_minima,
            'escala_maxima': criterio.escala_maxima,
            'opciones': criterio.opciones or [],
            'es_obligatorio': criterio.es_obligatorio,
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Criterio de revisión creado exitosamente',
            'data': criterio_dict
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
            'error': f'Error al crear criterio de revisión: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def criterio_detail(request, criterio_id):
    """Obtiene los detalles de un criterio de revisión"""
    try:
        criterio = get_object_or_404(CriterioRevision, id=criterio_id)
        
        criterio_dict = {
            'id': criterio.id,
            'nombre': criterio.nombre,
            'descripcion': criterio.descripcion or '',
            'tipo': criterio.tipo,
            'tipo_display': criterio.get_tipo_display(),
            'escala_minima': criterio.escala_minima,
            'escala_maxima': criterio.escala_maxima,
            'opciones': criterio.opciones or [],
            'es_obligatorio': criterio.es_obligatorio,
        }
        
        return JsonResponse({
            'success': True,
            'data': criterio_dict
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener criterio de revisión: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "PUT"])
def criterio_update(request, criterio_id):
    """Actualiza un criterio de revisión existente"""
    try:
        criterio = get_object_or_404(CriterioRevision, id=criterio_id)
        
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
        
        # Validar campos requeridos
        nombre = data.get('nombre', '').strip()
        if not nombre:
            return JsonResponse({
                'success': False,
                'error': 'El nombre es obligatorio'
            }, status=400)
        
        tipo = data.get('tipo', criterio.tipo)
        escala_minima = data.get('escala_minima')
        escala_maxima = data.get('escala_maxima')
        opciones = data.get('opciones')
        
        # Validar según el tipo
        if tipo == 'numerico':
            if escala_minima is None or escala_maxima is None:
                return JsonResponse({
                    'success': False,
                    'error': 'La escala mínima y máxima son obligatorias para criterios numéricos'
                }, status=400)
            if escala_minima >= escala_maxima:
                return JsonResponse({
                    'success': False,
                    'error': 'La escala mínima debe ser menor que la máxima'
                }, status=400)
        elif tipo == 'opcion':
            if not opciones or not isinstance(opciones, list) or len(opciones) == 0:
                return JsonResponse({
                    'success': False,
                    'error': 'Las opciones son obligatorias para criterios de tipo opción'
                }, status=400)
        
        # Actualizar campos
        criterio.nombre = nombre
        criterio.descripcion = data.get('descripcion', '').strip() or None
        criterio.tipo = tipo
        criterio.escala_minima = escala_minima
        criterio.escala_maxima = escala_maxima
        criterio.opciones = opciones if tipo == 'opcion' else None
        criterio.es_obligatorio = data.get('es_obligatorio', False)
        
        criterio.full_clean()
        criterio.save()
        
        # Retornar los datos actualizados
        criterio_dict = {
            'id': criterio.id,
            'nombre': criterio.nombre,
            'descripcion': criterio.descripcion or '',
            'tipo': criterio.tipo,
            'tipo_display': criterio.get_tipo_display(),
            'escala_minima': criterio.escala_minima,
            'escala_maxima': criterio.escala_maxima,
            'opciones': criterio.opciones or [],
            'es_obligatorio': criterio.es_obligatorio,
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Criterio de revisión actualizado exitosamente',
            'data': criterio_dict
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
            'error': f'Error al actualizar criterio de revisión: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "DELETE"])
def criterio_delete(request, criterio_id):
    """Elimina un criterio de revisión"""
    try:
        criterio = get_object_or_404(CriterioRevision, id=criterio_id)
        
        # Manejar tanto POST con _method como DELETE directo
        if request.method == 'POST':
            data = json.loads(request.body) if request.body else {}
            if data.get('_method') != 'DELETE':
                return JsonResponse({
                    'success': False,
                    'error': 'Método no permitido'
                }, status=405)
        
        # Verificar si hay evaluaciones asociadas
        if EvaluacionCriterio.objects.filter(criterio=criterio).exists():
            return JsonResponse({
                'success': False,
                'error': 'No se puede eliminar el criterio porque tiene evaluaciones asociadas'
            }, status=400)
        
        # Eliminar el criterio
        criterio.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Criterio de revisión eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al eliminar criterio de revisión: {str(e)}'
        }, status=500)


# ============================================================================
# VISTAS PARA PROCESOS DE REVISIÓN
# ============================================================================

@login_required
@require_http_methods(["GET"])
def procesos_list(request):
    """Lista todos los procesos de revisión en formato JSON"""
    procesos = ProcesoRevision.objects.select_related('documento', 'iniciado_por').all()
    procesos_data = []
    
    for proceso in procesos:
        documento_titulo = proceso.documento.get_titulo() if hasattr(proceso.documento, 'get_titulo') else (proceso.documento.titulo or f'Documento #{proceso.documento.id}')
        iniciado_por_nombre = proceso.iniciado_por.get_full_name() if proceso.iniciado_por.get_full_name() else proceso.iniciado_por.username
        
        proceso_dict = {
            'id': proceso.id,
            'documento_id': proceso.documento.id,
            'documento_titulo': documento_titulo,
            'tipo_revision': proceso.tipo_revision,
            'tipo_revision_display': proceso.get_tipo_revision_display(),
            'estado': proceso.estado,
            'estado_display': proceso.get_estado_display(),
            'iniciado_por_id': proceso.iniciado_por.id,
            'iniciado_por_nombre': iniciado_por_nombre,
            'fecha_inicio': proceso.fecha_inicio.isoformat() if proceso.fecha_inicio else None,
            'fecha_finalizacion': proceso.fecha_finalizacion.isoformat() if proceso.fecha_finalizacion else None,
            'notas_generales': proceso.notas_generales or '',
            'revisiones_count': proceso.revisiones.count(),
        }
        procesos_data.append(proceso_dict)
    
    return JsonResponse({
        'success': True,
        'data': procesos_data,
        'total': len(procesos_data)
    })


@login_required
@require_http_methods(["POST"])
def proceso_create(request):
    """Crea un nuevo proceso de revisión"""
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
        
        tipo_revision = data.get('tipo_revision')
        if not tipo_revision:
            return JsonResponse({
                'success': False,
                'error': 'El tipo de revisión es obligatorio'
            }, status=400)
        
        # Crear el proceso
        proceso = ProcesoRevision(
            documento=documento,
            tipo_revision=tipo_revision,
            estado=data.get('estado', 'pendiente'),
            iniciado_por=request.user,
            notas_generales=data.get('notas_generales', '').strip() or None,
        )
        
        proceso.full_clean()
        proceso.save()
        
        # Retornar los datos del proceso creado
        documento_titulo = documento.get_titulo() if hasattr(documento, 'get_titulo') else (documento.titulo or f'Documento #{documento.id}')
        iniciado_por_nombre = request.user.get_full_name() if request.user.get_full_name() else request.user.username
        
        proceso_dict = {
            'id': proceso.id,
            'documento_id': proceso.documento.id,
            'documento_titulo': documento_titulo,
            'tipo_revision': proceso.tipo_revision,
            'tipo_revision_display': proceso.get_tipo_revision_display(),
            'estado': proceso.estado,
            'estado_display': proceso.get_estado_display(),
            'iniciado_por_id': proceso.iniciado_por.id,
            'iniciado_por_nombre': iniciado_por_nombre,
            'fecha_inicio': proceso.fecha_inicio.isoformat() if proceso.fecha_inicio else None,
            'fecha_finalizacion': proceso.fecha_finalizacion.isoformat() if proceso.fecha_finalizacion else None,
            'notas_generales': proceso.notas_generales or '',
            'revisiones_count': 0,
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Proceso de revisión creado exitosamente',
            'data': proceso_dict
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
            'error': f'Error al crear proceso de revisión: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def proceso_detail(request, proceso_id):
    """Obtiene los detalles de un proceso de revisión"""
    try:
        proceso = get_object_or_404(ProcesoRevision.objects.select_related('documento', 'iniciado_por'), id=proceso_id)
        
        documento_titulo = proceso.documento.get_titulo() if hasattr(proceso.documento, 'get_titulo') else (proceso.documento.titulo or f'Documento #{proceso.documento.id}')
        iniciado_por_nombre = proceso.iniciado_por.get_full_name() if proceso.iniciado_por.get_full_name() else proceso.iniciado_por.username
        
        proceso_dict = {
            'id': proceso.id,
            'documento_id': proceso.documento.id,
            'documento_titulo': documento_titulo,
            'tipo_revision': proceso.tipo_revision,
            'tipo_revision_display': proceso.get_tipo_revision_display(),
            'estado': proceso.estado,
            'estado_display': proceso.get_estado_display(),
            'iniciado_por_id': proceso.iniciado_por.id,
            'iniciado_por_nombre': iniciado_por_nombre,
            'fecha_inicio': proceso.fecha_inicio.isoformat() if proceso.fecha_inicio else None,
            'fecha_finalizacion': proceso.fecha_finalizacion.isoformat() if proceso.fecha_finalizacion else None,
            'notas_generales': proceso.notas_generales or '',
        }
        
        return JsonResponse({
            'success': True,
            'data': proceso_dict
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener proceso de revisión: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "PUT"])
def proceso_update(request, proceso_id):
    """Actualiza un proceso de revisión existente"""
    try:
        proceso = get_object_or_404(ProcesoRevision, id=proceso_id)
        
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
        
        # Validar documento si se cambia
        if 'documento_id' in data:
            documento_id = data.get('documento_id')
            if documento_id:
                documento = get_object_or_404(Documento, id=documento_id)
                proceso.documento = documento
        
        # Validar tipo de revisión
        if 'tipo_revision' in data:
            tipo_revision = data.get('tipo_revision')
            if tipo_revision:
                proceso.tipo_revision = tipo_revision
        
        # Actualizar otros campos
        if 'estado' in data:
            proceso.estado = data.get('estado')
        
        if 'notas_generales' in data:
            proceso.notas_generales = data.get('notas_generales', '').strip() or None
        
        # Si el estado cambia a aprobado o rechazado, establecer fecha_finalizacion
        if proceso.estado in ['aprobado', 'rechazado'] and not proceso.fecha_finalizacion:
            proceso.fecha_finalizacion = datetime.now()
        elif proceso.estado not in ['aprobado', 'rechazado']:
            proceso.fecha_finalizacion = None
        
        proceso.full_clean()
        proceso.save()
        
        # Retornar los datos actualizados
        documento_titulo = proceso.documento.get_titulo() if hasattr(proceso.documento, 'get_titulo') else (proceso.documento.titulo or f'Documento #{proceso.documento.id}')
        iniciado_por_nombre = proceso.iniciado_por.get_full_name() if proceso.iniciado_por.get_full_name() else proceso.iniciado_por.username
        
        proceso_dict = {
            'id': proceso.id,
            'documento_id': proceso.documento.id,
            'documento_titulo': documento_titulo,
            'tipo_revision': proceso.tipo_revision,
            'tipo_revision_display': proceso.get_tipo_revision_display(),
            'estado': proceso.estado,
            'estado_display': proceso.get_estado_display(),
            'iniciado_por_id': proceso.iniciado_por.id,
            'iniciado_por_nombre': iniciado_por_nombre,
            'fecha_inicio': proceso.fecha_inicio.isoformat() if proceso.fecha_inicio else None,
            'fecha_finalizacion': proceso.fecha_finalizacion.isoformat() if proceso.fecha_finalizacion else None,
            'notas_generales': proceso.notas_generales or '',
            'revisiones_count': proceso.revisiones.count(),
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Proceso de revisión actualizado exitosamente',
            'data': proceso_dict
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
            'error': f'Error al actualizar proceso de revisión: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "DELETE"])
def proceso_delete(request, proceso_id):
    """Elimina un proceso de revisión"""
    try:
        proceso = get_object_or_404(ProcesoRevision, id=proceso_id)
        
        # Manejar tanto POST con _method como DELETE directo
        if request.method == 'POST':
            data = json.loads(request.body) if request.body else {}
            if data.get('_method') != 'DELETE':
                return JsonResponse({
                    'success': False,
                    'error': 'Método no permitido'
                }, status=405)
        
        # Eliminar el proceso (las revisiones y evaluaciones se eliminan en cascada)
        proceso.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Proceso de revisión eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al eliminar proceso de revisión: {str(e)}'
        }, status=500)


# ============================================================================
# VISTAS PARA REVISIONES
# ============================================================================

@login_required
@require_http_methods(["GET"])
def revisiones_list(request):
    """Lista todas las revisiones en formato JSON"""
    revisiones = Revision.objects.select_related('proceso_revision', 'proceso_revision__documento', 'revisor').all()
    revisiones_data = []
    
    for revision in revisiones:
        revisor_nombre = revision.revisor.get_full_name() if revision.revisor.get_full_name() else revision.revisor.username
        documento_titulo = revision.proceso_revision.documento.get_titulo() if hasattr(revision.proceso_revision.documento, 'get_titulo') else (revision.proceso_revision.documento.titulo or f'Documento #{revision.proceso_revision.documento.id}')
        
        revision_dict = {
            'id': revision.id,
            'proceso_revision_id': revision.proceso_revision.id,
            'proceso_revision_texto': f"{documento_titulo} - {revision.proceso_revision.get_tipo_revision_display()}",
            'revisor_id': revision.revisor.id,
            'revisor_nombre': revisor_nombre,
            'estado': revision.estado,
            'estado_display': revision.get_estado_display(),
            'calificacion_general': revision.calificacion_general,
            'comentarios_publicos': revision.comentarios_publicos or '',
            'comentarios_privados': revision.comentarios_privados or '',
            'recomendacion': revision.recomendacion,
            'recomendacion_display': revision.get_recomendacion_display() if revision.recomendacion else '',
            'fecha_asignacion': revision.fecha_asignacion.isoformat() if revision.fecha_asignacion else None,
            'fecha_completacion': revision.fecha_completacion.isoformat() if revision.fecha_completacion else None,
        }
        revisiones_data.append(revision_dict)
    
    return JsonResponse({
        'success': True,
        'data': revisiones_data,
        'total': len(revisiones_data)
    })


@login_required
@require_http_methods(["POST"])
def revision_create(request):
    """Crea una nueva revisión"""
    try:
        data = json.loads(request.body)
        
        # Validar campos requeridos
        proceso_revision_id = data.get('proceso_revision_id')
        if not proceso_revision_id:
            return JsonResponse({
                'success': False,
                'error': 'El proceso de revisión es obligatorio'
            }, status=400)
        
        proceso_revision = get_object_or_404(ProcesoRevision, id=proceso_revision_id)
        
        revisor_id = data.get('revisor_id')
        if not revisor_id:
            return JsonResponse({
                'success': False,
                'error': 'El revisor es obligatorio'
            }, status=400)
        
        revisor = get_object_or_404(User, id=revisor_id)
        
        # Crear la revisión
        revision = Revision(
            proceso_revision=proceso_revision,
            revisor=revisor,
            estado=data.get('estado', 'asignado'),
            calificacion_general=data.get('calificacion_general'),
            comentarios_publicos=data.get('comentarios_publicos', '').strip() or None,
            comentarios_privados=data.get('comentarios_privados', '').strip() or None,
            recomendacion=data.get('recomendacion') or None,
        )
        
        revision.full_clean()
        revision.save()
        
        # Retornar los datos de la revisión creada
        revisor_nombre = revisor.get_full_name() if revisor.get_full_name() else revisor.username
        documento_titulo = proceso_revision.documento.get_titulo() if hasattr(proceso_revision.documento, 'get_titulo') else (proceso_revision.documento.titulo or f'Documento #{proceso_revision.documento.id}')
        
        revision_dict = {
            'id': revision.id,
            'proceso_revision_id': revision.proceso_revision.id,
            'proceso_revision_texto': f"{documento_titulo} - {proceso_revision.get_tipo_revision_display()}",
            'revisor_id': revision.revisor.id,
            'revisor_nombre': revisor_nombre,
            'estado': revision.estado,
            'estado_display': revision.get_estado_display(),
            'calificacion_general': revision.calificacion_general,
            'comentarios_publicos': revision.comentarios_publicos or '',
            'comentarios_privados': revision.comentarios_privados or '',
            'recomendacion': revision.recomendacion,
            'recomendacion_display': revision.get_recomendacion_display() if revision.recomendacion else '',
            'fecha_asignacion': revision.fecha_asignacion.isoformat() if revision.fecha_asignacion else None,
            'fecha_completacion': revision.fecha_completacion.isoformat() if revision.fecha_completacion else None,
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Revisión creada exitosamente',
            'data': revision_dict
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
            'error': f'Error al crear revisión: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def revision_detail(request, revision_id):
    """Obtiene los detalles de una revisión"""
    try:
        revision = get_object_or_404(Revision.objects.select_related('proceso_revision', 'proceso_revision__documento', 'revisor'), id=revision_id)
        
        revisor_nombre = revision.revisor.get_full_name() if revision.revisor.get_full_name() else revision.revisor.username
        documento_titulo = revision.proceso_revision.documento.get_titulo() if hasattr(revision.proceso_revision.documento, 'get_titulo') else (revision.proceso_revision.documento.titulo or f'Documento #{revision.proceso_revision.documento.id}')
        
        revision_dict = {
            'id': revision.id,
            'proceso_revision_id': revision.proceso_revision.id,
            'proceso_revision_texto': f"{documento_titulo} - {revision.proceso_revision.get_tipo_revision_display()}",
            'revisor_id': revision.revisor.id,
            'revisor_nombre': revisor_nombre,
            'estado': revision.estado,
            'estado_display': revision.get_estado_display(),
            'calificacion_general': revision.calificacion_general,
            'comentarios_publicos': revision.comentarios_publicos or '',
            'comentarios_privados': revision.comentarios_privados or '',
            'recomendacion': revision.recomendacion,
            'recomendacion_display': revision.get_recomendacion_display() if revision.recomendacion else '',
            'fecha_asignacion': revision.fecha_asignacion.isoformat() if revision.fecha_asignacion else None,
            'fecha_completacion': revision.fecha_completacion.isoformat() if revision.fecha_completacion else None,
        }
        
        return JsonResponse({
            'success': True,
            'data': revision_dict
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener revisión: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "PUT"])
def revision_update(request, revision_id):
    """Actualiza una revisión existente"""
    try:
        revision = get_object_or_404(Revision, id=revision_id)
        
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
        
        # Validar proceso de revisión si se cambia
        if 'proceso_revision_id' in data:
            proceso_revision_id = data.get('proceso_revision_id')
            if proceso_revision_id:
                proceso_revision = get_object_or_404(ProcesoRevision, id=proceso_revision_id)
                revision.proceso_revision = proceso_revision
        
        # Validar revisor si se cambia
        if 'revisor_id' in data:
            revisor_id = data.get('revisor_id')
            if revisor_id:
                revisor = get_object_or_404(User, id=revisor_id)
                revision.revisor = revisor
        
        # Actualizar otros campos
        if 'estado' in data:
            revision.estado = data.get('estado')
            
            # Si el estado cambia a completado, establecer fecha_completacion
            if revision.estado == 'completado' and not revision.fecha_completacion:
                revision.fecha_completacion = datetime.now()
            elif revision.estado != 'completado':
                revision.fecha_completacion = None
        
        if 'calificacion_general' in data:
            calificacion = data.get('calificacion_general')
            revision.calificacion_general = calificacion if calificacion else None
        
        if 'comentarios_publicos' in data:
            revision.comentarios_publicos = data.get('comentarios_publicos', '').strip() or None
        
        if 'comentarios_privados' in data:
            revision.comentarios_privados = data.get('comentarios_privados', '').strip() or None
        
        if 'recomendacion' in data:
            revision.recomendacion = data.get('recomendacion') or None
        
        revision.full_clean()
        revision.save()
        
        # Retornar los datos actualizados
        revisor_nombre = revision.revisor.get_full_name() if revision.revisor.get_full_name() else revision.revisor.username
        documento_titulo = revision.proceso_revision.documento.get_titulo() if hasattr(revision.proceso_revision.documento, 'get_titulo') else (revision.proceso_revision.documento.titulo or f'Documento #{revision.proceso_revision.documento.id}')
        
        revision_dict = {
            'id': revision.id,
            'proceso_revision_id': revision.proceso_revision.id,
            'proceso_revision_texto': f"{documento_titulo} - {revision.proceso_revision.get_tipo_revision_display()}",
            'revisor_id': revision.revisor.id,
            'revisor_nombre': revisor_nombre,
            'estado': revision.estado,
            'estado_display': revision.get_estado_display(),
            'calificacion_general': revision.calificacion_general,
            'comentarios_publicos': revision.comentarios_publicos or '',
            'comentarios_privados': revision.comentarios_privados or '',
            'recomendacion': revision.recomendacion,
            'recomendacion_display': revision.get_recomendacion_display() if revision.recomendacion else '',
            'fecha_asignacion': revision.fecha_asignacion.isoformat() if revision.fecha_asignacion else None,
            'fecha_completacion': revision.fecha_completacion.isoformat() if revision.fecha_completacion else None,
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Revisión actualizada exitosamente',
            'data': revision_dict
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
            'error': f'Error al actualizar revisión: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "DELETE"])
def revision_delete(request, revision_id):
    """Elimina una revisión"""
    try:
        revision = get_object_or_404(Revision, id=revision_id)
        
        # Manejar tanto POST con _method como DELETE directo
        if request.method == 'POST':
            data = json.loads(request.body) if request.body else {}
            if data.get('_method') != 'DELETE':
                return JsonResponse({
                    'success': False,
                    'error': 'Método no permitido'
                }, status=405)
        
        # Eliminar la revisión (las evaluaciones se eliminan en cascada)
        revision.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Revisión eliminada exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al eliminar revisión: {str(e)}'
        }, status=500)


# ============================================================================
# VISTAS PARA EVALUACIONES DE CRITERIOS
# ============================================================================

@login_required
@require_http_methods(["GET"])
def evaluaciones_list(request):
    """Lista todas las evaluaciones de criterios en formato JSON"""
    evaluaciones = EvaluacionCriterio.objects.select_related('revision', 'revision__proceso_revision', 'revision__proceso_revision__documento', 'criterio').all()
    evaluaciones_data = []
    
    for evaluacion in evaluaciones:
        # Obtener el valor según el tipo del criterio
        valor = None
        if evaluacion.criterio.tipo == 'numerico':
            valor = evaluacion.valor_numerico
        elif evaluacion.criterio.tipo == 'texto':
            valor = evaluacion.valor_texto
        elif evaluacion.criterio.tipo == 'booleano':
            valor = evaluacion.valor_booleano
        elif evaluacion.criterio.tipo == 'opcion':
            valor = evaluacion.valor_opcion
        
        revisor_nombre = evaluacion.revision.revisor.get_full_name() if evaluacion.revision.revisor.get_full_name() else evaluacion.revision.revisor.username
        documento_titulo = evaluacion.revision.proceso_revision.documento.get_titulo() if hasattr(evaluacion.revision.proceso_revision.documento, 'get_titulo') else (evaluacion.revision.proceso_revision.documento.titulo or f'Doc #{evaluacion.revision.proceso_revision.documento.id}')
        
        evaluacion_dict = {
            'id': evaluacion.id,
            'revision_id': evaluacion.revision.id,
            'revision_texto': f"{documento_titulo} - {revisor_nombre}",
            'criterio_id': evaluacion.criterio.id,
            'criterio_nombre': evaluacion.criterio.nombre,
            'criterio_tipo': evaluacion.criterio.tipo,
            'valor_numerico': evaluacion.valor_numerico,
            'valor_texto': evaluacion.valor_texto,
            'valor_booleano': evaluacion.valor_booleano,
            'valor_opcion': evaluacion.valor_opcion,
            'valor': valor,
            'comentarios': evaluacion.comentarios or '',
        }
        evaluaciones_data.append(evaluacion_dict)
    
    return JsonResponse({
        'success': True,
        'data': evaluaciones_data,
        'total': len(evaluaciones_data)
    })


@login_required
@require_http_methods(["POST"])
def evaluacion_create(request):
    """Crea una nueva evaluación de criterio"""
    try:
        data = json.loads(request.body)
        
        # Validar campos requeridos
        revision_id = data.get('revision_id')
        if not revision_id:
            return JsonResponse({
                'success': False,
                'error': 'La revisión es obligatoria'
            }, status=400)
        
        revision = get_object_or_404(Revision, id=revision_id)
        
        criterio_id = data.get('criterio_id')
        if not criterio_id:
            return JsonResponse({
                'success': False,
                'error': 'El criterio es obligatorio'
            }, status=400)
        
        criterio = get_object_or_404(CriterioRevision, id=criterio_id)
        
        # Verificar que no exista ya una evaluación para esta revisión y criterio
        if EvaluacionCriterio.objects.filter(revision=revision, criterio=criterio).exists():
            return JsonResponse({
                'success': False,
                'error': 'Ya existe una evaluación para este criterio en esta revisión'
            }, status=400)
        
        # Validar y obtener el valor según el tipo del criterio
        valor_numerico = None
        valor_texto = None
        valor_booleano = None
        valor_opcion = None
        
        if criterio.tipo == 'numerico':
            valor_numerico = data.get('valor_numerico')
            if valor_numerico is None and criterio.es_obligatorio:
                return JsonResponse({
                    'success': False,
                    'error': 'El valor numérico es obligatorio para este criterio'
                }, status=400)
            if valor_numerico is not None:
                if criterio.escala_minima is not None and valor_numerico < criterio.escala_minima:
                    return JsonResponse({
                        'success': False,
                        'error': f'El valor debe ser mayor o igual a {criterio.escala_minima}'
                    }, status=400)
                if criterio.escala_maxima is not None and valor_numerico > criterio.escala_maxima:
                    return JsonResponse({
                        'success': False,
                        'error': f'El valor debe ser menor o igual a {criterio.escala_maxima}'
                    }, status=400)
        elif criterio.tipo == 'texto':
            valor_texto = data.get('valor_texto', '').strip()
            if not valor_texto and criterio.es_obligatorio:
                return JsonResponse({
                    'success': False,
                    'error': 'El valor de texto es obligatorio para este criterio'
                }, status=400)
            valor_texto = valor_texto or None
        elif criterio.tipo == 'booleano':
            valor_booleano = data.get('valor_booleano')
            if valor_booleano is None and criterio.es_obligatorio:
                return JsonResponse({
                    'success': False,
                    'error': 'El valor booleano es obligatorio para este criterio'
                }, status=400)
        elif criterio.tipo == 'opcion':
            valor_opcion = data.get('valor_opcion', '').strip()
            if not valor_opcion and criterio.es_obligatorio:
                return JsonResponse({
                    'success': False,
                    'error': 'El valor de opción es obligatorio para este criterio'
                }, status=400)
            if valor_opcion and criterio.opciones:
                if valor_opcion not in criterio.opciones:
                    return JsonResponse({
                        'success': False,
                        'error': f'El valor debe ser una de las opciones válidas: {", ".join(criterio.opciones)}'
                    }, status=400)
            valor_opcion = valor_opcion or None
        
        # Crear la evaluación
        evaluacion = EvaluacionCriterio(
            revision=revision,
            criterio=criterio,
            valor_numerico=valor_numerico,
            valor_texto=valor_texto,
            valor_booleano=valor_booleano,
            valor_opcion=valor_opcion,
            comentarios=data.get('comentarios', '').strip() or None,
        )
        
        evaluacion.full_clean()
        evaluacion.save()
        
        # Retornar los datos de la evaluación creada
        valor = valor_numerico if criterio.tipo == 'numerico' else (valor_texto if criterio.tipo == 'texto' else (valor_booleano if criterio.tipo == 'booleano' else valor_opcion))
        revisor_nombre = revision.revisor.get_full_name() if revision.revisor.get_full_name() else revision.revisor.username
        documento_titulo = revision.proceso_revision.documento.get_titulo() if hasattr(revision.proceso_revision.documento, 'get_titulo') else (revision.proceso_revision.documento.titulo or f'Doc #{revision.proceso_revision.documento.id}')
        
        evaluacion_dict = {
            'id': evaluacion.id,
            'revision_id': evaluacion.revision.id,
            'revision_texto': f"{documento_titulo} - {revisor_nombre}",
            'criterio_id': evaluacion.criterio.id,
            'criterio_nombre': evaluacion.criterio.nombre,
            'criterio_tipo': evaluacion.criterio.tipo,
            'valor_numerico': evaluacion.valor_numerico,
            'valor_texto': evaluacion.valor_texto,
            'valor_booleano': evaluacion.valor_booleano,
            'valor_opcion': evaluacion.valor_opcion,
            'valor': valor,
            'comentarios': evaluacion.comentarios or '',
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Evaluación de criterio creada exitosamente',
            'data': evaluacion_dict
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
            'error': f'Error al crear evaluación de criterio: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def evaluacion_detail(request, evaluacion_id):
    """Obtiene los detalles de una evaluación de criterio"""
    try:
        evaluacion = get_object_or_404(EvaluacionCriterio.objects.select_related('revision', 'revision__proceso_revision', 'revision__proceso_revision__documento', 'criterio'), id=evaluacion_id)
        
        # Obtener el valor según el tipo del criterio
        valor = None
        if evaluacion.criterio.tipo == 'numerico':
            valor = evaluacion.valor_numerico
        elif evaluacion.criterio.tipo == 'texto':
            valor = evaluacion.valor_texto
        elif evaluacion.criterio.tipo == 'booleano':
            valor = evaluacion.valor_booleano
        elif evaluacion.criterio.tipo == 'opcion':
            valor = evaluacion.valor_opcion
        
        revisor_nombre = evaluacion.revision.revisor.get_full_name() if evaluacion.revision.revisor.get_full_name() else evaluacion.revision.revisor.username
        documento_titulo = evaluacion.revision.proceso_revision.documento.get_titulo() if hasattr(evaluacion.revision.proceso_revision.documento, 'get_titulo') else (evaluacion.revision.proceso_revision.documento.titulo or f'Doc #{evaluacion.revision.proceso_revision.documento.id}')
        
        evaluacion_dict = {
            'id': evaluacion.id,
            'revision_id': evaluacion.revision.id,
            'revision_texto': f"{documento_titulo} - {revisor_nombre}",
            'criterio_id': evaluacion.criterio.id,
            'criterio_nombre': evaluacion.criterio.nombre,
            'criterio_tipo': evaluacion.criterio.tipo,
            'criterio_escala_minima': evaluacion.criterio.escala_minima,
            'criterio_escala_maxima': evaluacion.criterio.escala_maxima,
            'criterio_opciones': evaluacion.criterio.opciones or [],
            'valor_numerico': evaluacion.valor_numerico,
            'valor_texto': evaluacion.valor_texto,
            'valor_booleano': evaluacion.valor_booleano,
            'valor_opcion': evaluacion.valor_opcion,
            'valor': valor,
            'comentarios': evaluacion.comentarios or '',
        }
        
        return JsonResponse({
            'success': True,
            'data': evaluacion_dict
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener evaluación de criterio: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "PUT"])
def evaluacion_update(request, evaluacion_id):
    """Actualiza una evaluación de criterio existente"""
    try:
        evaluacion = get_object_or_404(EvaluacionCriterio.objects.select_related('criterio'), id=evaluacion_id)
        criterio = evaluacion.criterio
        
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
        
        # Validar revisión si se cambia
        if 'revision_id' in data:
            revision_id = data.get('revision_id')
            if revision_id:
                revision = get_object_or_404(Revision, id=revision_id)
                # Verificar que no exista ya una evaluación para esta revisión y criterio (excepto la actual)
                if EvaluacionCriterio.objects.filter(revision=revision, criterio=criterio).exclude(id=evaluacion_id).exists():
                    return JsonResponse({
                        'success': False,
                        'error': 'Ya existe una evaluación para este criterio en esta revisión'
                    }, status=400)
                evaluacion.revision = revision
        
        # Validar criterio si se cambia
        if 'criterio_id' in data:
            criterio_id = data.get('criterio_id')
            if criterio_id and criterio_id != criterio.id:
                nuevo_criterio = get_object_or_404(CriterioRevision, id=criterio_id)
                # Verificar que no exista ya una evaluación para esta revisión y nuevo criterio
                if EvaluacionCriterio.objects.filter(revision=evaluacion.revision, criterio=nuevo_criterio).exclude(id=evaluacion_id).exists():
                    return JsonResponse({
                        'success': False,
                        'error': 'Ya existe una evaluación para este criterio en esta revisión'
                    }, status=400)
                criterio = nuevo_criterio
                evaluacion.criterio = criterio
        
        # Limpiar todos los valores primero
        evaluacion.valor_numerico = None
        evaluacion.valor_texto = None
        evaluacion.valor_booleano = None
        evaluacion.valor_opcion = None
        
        # Validar y establecer el valor según el tipo del criterio
        if criterio.tipo == 'numerico':
            valor_numerico = data.get('valor_numerico')
            if valor_numerico is None and criterio.es_obligatorio:
                return JsonResponse({
                    'success': False,
                    'error': 'El valor numérico es obligatorio para este criterio'
                }, status=400)
            if valor_numerico is not None:
                if criterio.escala_minima is not None and valor_numerico < criterio.escala_minima:
                    return JsonResponse({
                        'success': False,
                        'error': f'El valor debe ser mayor o igual a {criterio.escala_minima}'
                    }, status=400)
                if criterio.escala_maxima is not None and valor_numerico > criterio.escala_maxima:
                    return JsonResponse({
                        'success': False,
                        'error': f'El valor debe ser menor o igual a {criterio.escala_maxima}'
                    }, status=400)
            evaluacion.valor_numerico = valor_numerico
        elif criterio.tipo == 'texto':
            valor_texto = data.get('valor_texto', '').strip()
            if not valor_texto and criterio.es_obligatorio:
                return JsonResponse({
                    'success': False,
                    'error': 'El valor de texto es obligatorio para este criterio'
                }, status=400)
            evaluacion.valor_texto = valor_texto or None
        elif criterio.tipo == 'booleano':
            valor_booleano = data.get('valor_booleano')
            if valor_booleano is None and criterio.es_obligatorio:
                return JsonResponse({
                    'success': False,
                    'error': 'El valor booleano es obligatorio para este criterio'
                }, status=400)
            evaluacion.valor_booleano = valor_booleano
        elif criterio.tipo == 'opcion':
            valor_opcion = data.get('valor_opcion', '').strip()
            if not valor_opcion and criterio.es_obligatorio:
                return JsonResponse({
                    'success': False,
                    'error': 'El valor de opción es obligatorio para este criterio'
                }, status=400)
            if valor_opcion and criterio.opciones:
                if valor_opcion not in criterio.opciones:
                    return JsonResponse({
                        'success': False,
                        'error': f'El valor debe ser una de las opciones válidas: {", ".join(criterio.opciones)}'
                    }, status=400)
            evaluacion.valor_opcion = valor_opcion or None
        
        # Actualizar comentarios
        if 'comentarios' in data:
            evaluacion.comentarios = data.get('comentarios', '').strip() or None
        
        evaluacion.full_clean()
        evaluacion.save()
        
        # Retornar los datos actualizados
        valor = evaluacion.valor_numerico if criterio.tipo == 'numerico' else (evaluacion.valor_texto if criterio.tipo == 'texto' else (evaluacion.valor_booleano if criterio.tipo == 'booleano' else evaluacion.valor_opcion))
        revisor_nombre = evaluacion.revision.revisor.get_full_name() if evaluacion.revision.revisor.get_full_name() else evaluacion.revision.revisor.username
        documento_titulo = evaluacion.revision.proceso_revision.documento.get_titulo() if hasattr(evaluacion.revision.proceso_revision.documento, 'get_titulo') else (evaluacion.revision.proceso_revision.documento.titulo or f'Doc #{evaluacion.revision.proceso_revision.documento.id}')
        
        evaluacion_dict = {
            'id': evaluacion.id,
            'revision_id': evaluacion.revision.id,
            'revision_texto': f"{documento_titulo} - {revisor_nombre}",
            'criterio_id': evaluacion.criterio.id,
            'criterio_nombre': evaluacion.criterio.nombre,
            'criterio_tipo': evaluacion.criterio.tipo,
            'valor_numerico': evaluacion.valor_numerico,
            'valor_texto': evaluacion.valor_texto,
            'valor_booleano': evaluacion.valor_booleano,
            'valor_opcion': evaluacion.valor_opcion,
            'valor': valor,
            'comentarios': evaluacion.comentarios or '',
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Evaluación de criterio actualizada exitosamente',
            'data': evaluacion_dict
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
            'error': f'Error al actualizar evaluación de criterio: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "DELETE"])
def evaluacion_delete(request, evaluacion_id):
    """Elimina una evaluación de criterio"""
    try:
        evaluacion = get_object_or_404(EvaluacionCriterio, id=evaluacion_id)
        
        # Manejar tanto POST con _method como DELETE directo
        if request.method == 'POST':
            data = json.loads(request.body) if request.body else {}
            if data.get('_method') != 'DELETE':
                return JsonResponse({
                    'success': False,
                    'error': 'Método no permitido'
                }, status=405)
        
        # Eliminar la evaluación
        evaluacion.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Evaluación de criterio eliminada exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al eliminar evaluación de criterio: {str(e)}'
        }, status=500)
