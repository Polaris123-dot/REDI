from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from datetime import datetime
import json
from .models import IndiceBusqueda, Busqueda
from repositorio.models import Documento
from django.contrib.auth.models import User


@login_required
@ensure_csrf_cookie
@require_http_methods(["GET"])
def index(request):
    """Vista principal de búsqueda"""
    # Verificar permisos
    if not (request.user.has_perm('busqueda.view_indicebusqueda') or 
            request.user.has_perm('busqueda.view_busqueda') or
            request.user.is_superuser):
        messages.warning(request, 'No tienes permisos para acceder a búsqueda.')
        return redirect('usuarios:panel')
    return render(request, 'busqueda/index.html')


# ============================================================================
# VISTAS AUXILIARES PARA SELECTS
# ============================================================================

@login_required
@require_http_methods(["GET"])
def documentos_for_select(request):
    """Obtiene los documentos para usar en selects (solo los que no tienen índice, o todos si se especifica incluir_con_indice)"""
    try:
        incluir_con_indice = request.GET.get('incluir_con_indice', 'false').lower() == 'true'
        indice_id_excluir = request.GET.get('indice_id_excluir', None)
        
        if incluir_con_indice and indice_id_excluir:
            # Si se está editando, incluir todos los documentos, pero excluir el índice actual
            try:
                indice_actual = IndiceBusqueda.objects.get(id=indice_id_excluir)
                documento_id_actual = indice_actual.documento_id
                documentos = Documento.objects.select_related('proyecto', 'tipo_recurso', 'estado').all()
            except IndiceBusqueda.DoesNotExist:
                # Si no existe el índice, solo mostrar documentos sin índice
                documentos_con_indice = IndiceBusqueda.objects.values_list('documento_id', flat=True)
                documentos = Documento.objects.select_related('proyecto', 'tipo_recurso', 'estado').exclude(id__in=documentos_con_indice)
                documento_id_actual = None
        else:
            # Por defecto, solo documentos que no tienen índice
            documentos_con_indice = IndiceBusqueda.objects.values_list('documento_id', flat=True)
            documentos = Documento.objects.select_related('proyecto', 'tipo_recurso', 'estado').exclude(id__in=documentos_con_indice)
            documento_id_actual = None
        
        documentos_data = []
        
        for documento in documentos:
            titulo = documento.get_titulo() if hasattr(documento, 'get_titulo') else (documento.titulo or f'Documento #{documento.id}')
            documentos_data.append({
                'id': documento.id,
                'text': titulo,
                'handle': documento.handle or '',
                'proyecto_titulo': documento.proyecto.titulo if documento.proyecto else '',
                'tiene_indice': IndiceBusqueda.objects.filter(documento_id=documento.id).exists() and documento.id != documento_id_actual,
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
# VISTAS PARA ÍNDICES DE BÚSQUEDA
# ============================================================================

@login_required
@require_http_methods(["GET"])
def indices_list(request):
    """Lista todos los índices de búsqueda en formato JSON"""
    indices = IndiceBusqueda.objects.select_related('documento').all()
    indices_data = []
    
    for indice in indices:
        indice_dict = {
            'id': indice.id,
            'documento_id': indice.documento.id,
            'documento_titulo': indice.documento.get_titulo() if hasattr(indice.documento, 'get_titulo') else (indice.documento.titulo or f'Documento #{indice.documento.id}'),
            'contenido_indexado_preview': indice.contenido_indexado[:100] + '...' if len(indice.contenido_indexado) > 100 else indice.contenido_indexado,
            'contenido_indexado_length': len(indice.contenido_indexado),
            'palabras_clave_indexadas': indice.palabras_clave_indexadas or '',
            'fecha_indexacion': indice.fecha_indexacion.isoformat() if indice.fecha_indexacion else None,
        }
        indices_data.append(indice_dict)
    
    return JsonResponse({
        'success': True,
        'data': indices_data,
        'total': len(indices_data)
    })


@login_required
@require_http_methods(["POST"])
def indice_create(request):
    """Crea un nuevo índice de búsqueda"""
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
        
        # Verificar que el documento no tenga ya un índice
        if IndiceBusqueda.objects.filter(documento=documento).exists():
            return JsonResponse({
                'success': False,
                'error': 'Este documento ya tiene un índice de búsqueda'
            }, status=400)
        
        contenido_indexado = data.get('contenido_indexado', '').strip()
        if not contenido_indexado:
            return JsonResponse({
                'success': False,
                'error': 'El contenido indexado es obligatorio'
            }, status=400)
        
        # Crear el índice
        indice = IndiceBusqueda(
            documento=documento,
            contenido_indexado=contenido_indexado,
            palabras_clave_indexadas=data.get('palabras_clave_indexadas', '').strip() or None,
        )
        
        indice.full_clean()
        indice.save()
        
        # Retornar los datos del índice creado
        indice_dict = {
            'id': indice.id,
            'documento_id': indice.documento.id,
            'documento_titulo': indice.documento.get_titulo() if hasattr(indice.documento, 'get_titulo') else (indice.documento.titulo or f'Documento #{indice.documento.id}'),
            'contenido_indexado_preview': indice.contenido_indexado[:100] + '...' if len(indice.contenido_indexado) > 100 else indice.contenido_indexado,
            'contenido_indexado_length': len(indice.contenido_indexado),
            'palabras_clave_indexadas': indice.palabras_clave_indexadas or '',
            'fecha_indexacion': indice.fecha_indexacion.isoformat() if indice.fecha_indexacion else None,
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Índice de búsqueda creado exitosamente',
            'data': indice_dict
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
            'error': f'Error al crear índice de búsqueda: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def indice_detail(request, indice_id):
    """Obtiene los detalles de un índice de búsqueda"""
    try:
        indice = get_object_or_404(IndiceBusqueda.objects.select_related('documento'), id=indice_id)
        
        indice_dict = {
            'id': indice.id,
            'documento_id': indice.documento.id,
            'documento_titulo': indice.documento.get_titulo() if hasattr(indice.documento, 'get_titulo') else (indice.documento.titulo or f'Documento #{indice.documento.id}'),
            'contenido_indexado': indice.contenido_indexado,
            'contenido_indexado_length': len(indice.contenido_indexado),
            'palabras_clave_indexadas': indice.palabras_clave_indexadas or '',
            'fecha_indexacion': indice.fecha_indexacion.isoformat() if indice.fecha_indexacion else None,
        }
        
        return JsonResponse({
            'success': True,
            'data': indice_dict
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener índice de búsqueda: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "PUT"])
def indice_update(request, indice_id):
    """Actualiza un índice de búsqueda existente"""
    try:
        indice = get_object_or_404(IndiceBusqueda, id=indice_id)
        
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
        
        # Validar contenido indexado
        contenido_indexado = data.get('contenido_indexado', '').strip()
        if not contenido_indexado:
            return JsonResponse({
                'success': False,
                'error': 'El contenido indexado es obligatorio'
            }, status=400)
        
        # Si se cambia el documento, verificar que el nuevo documento no tenga índice
        if 'documento_id' in data:
            nuevo_documento_id = data.get('documento_id')
            if nuevo_documento_id != indice.documento.id:
                nuevo_documento = get_object_or_404(Documento, id=nuevo_documento_id)
                # Verificar que el nuevo documento no tenga índice
                if IndiceBusqueda.objects.filter(documento=nuevo_documento).exclude(id=indice_id).exists():
                    return JsonResponse({
                        'success': False,
                        'error': 'El documento seleccionado ya tiene un índice de búsqueda'
                    }, status=400)
                indice.documento = nuevo_documento
        
        # Actualizar campos
        indice.contenido_indexado = contenido_indexado
        indice.palabras_clave_indexadas = data.get('palabras_clave_indexadas', '').strip() or None
        
        indice.full_clean()
        indice.save()
        
        # Retornar los datos actualizados
        indice_dict = {
            'id': indice.id,
            'documento_id': indice.documento.id,
            'documento_titulo': indice.documento.get_titulo() if hasattr(indice.documento, 'get_titulo') else (indice.documento.titulo or f'Documento #{indice.documento.id}'),
            'contenido_indexado_preview': indice.contenido_indexado[:100] + '...' if len(indice.contenido_indexado) > 100 else indice.contenido_indexado,
            'contenido_indexado_length': len(indice.contenido_indexado),
            'palabras_clave_indexadas': indice.palabras_clave_indexadas or '',
            'fecha_indexacion': indice.fecha_indexacion.isoformat() if indice.fecha_indexacion else None,
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Índice de búsqueda actualizado exitosamente',
            'data': indice_dict
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
            'error': f'Error al actualizar índice de búsqueda: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "DELETE"])
def indice_delete(request, indice_id):
    """Elimina un índice de búsqueda"""
    try:
        indice = get_object_or_404(IndiceBusqueda, id=indice_id)
        
        # Manejar tanto POST con _method como DELETE directo
        if request.method == 'POST':
            data = json.loads(request.body) if request.body else {}
            if data.get('_method') != 'DELETE':
                return JsonResponse({
                    'success': False,
                    'error': 'Método no permitido'
                }, status=405)
        
        # Eliminar el índice
        indice.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Índice de búsqueda eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al eliminar índice de búsqueda: {str(e)}'
        }, status=500)


# ============================================================================
# VISTAS PARA BÚSQUEDAS
# ============================================================================

@login_required
@require_http_methods(["GET"])
def busquedas_list(request):
    """Lista todas las búsquedas en formato JSON"""
    busquedas = Busqueda.objects.select_related('usuario').all()
    busquedas_data = []
    
    for busqueda in busquedas:
        busqueda_dict = {
            'id': busqueda.id,
            'usuario_id': busqueda.usuario.id if busqueda.usuario else None,
            'usuario_nombre': busqueda.usuario.get_full_name() if busqueda.usuario and busqueda.usuario.get_full_name() else (busqueda.usuario.username if busqueda.usuario else 'Anónimo'),
            'termino_busqueda': busqueda.termino_busqueda,
            'filtros_aplicados': busqueda.filtros_aplicados,
            'resultados_encontrados': busqueda.resultados_encontrados,
            'ip_address': str(busqueda.ip_address) if busqueda.ip_address else '',
            'fecha': busqueda.fecha.isoformat() if busqueda.fecha else None,
        }
        busquedas_data.append(busqueda_dict)
    
    return JsonResponse({
        'success': True,
        'data': busquedas_data,
        'total': len(busquedas_data)
    })


@login_required
@require_http_methods(["POST"])
def busqueda_create(request):
    """Crea una nueva búsqueda"""
    try:
        data = json.loads(request.body)
        
        # Validar campos requeridos
        termino_busqueda = data.get('termino_busqueda', '').strip()
        if not termino_busqueda:
            return JsonResponse({
                'success': False,
                'error': 'El término de búsqueda es obligatorio'
            }, status=400)
        
        # Procesar filtros_aplicados si es JSON
        filtros_aplicados = data.get('filtros_aplicados')
        if filtros_aplicados:
            if isinstance(filtros_aplicados, str):
                try:
                    filtros_aplicados = json.loads(filtros_aplicados)
                except json.JSONDecodeError:
                    return JsonResponse({
                        'success': False,
                        'error': 'filtros_aplicados debe ser un JSON válido'
                    }, status=400)
        else:
            filtros_aplicados = None
        
        # Crear la búsqueda
        busqueda = Busqueda(
            usuario_id=data.get('usuario_id') or None,
            termino_busqueda=termino_busqueda,
            filtros_aplicados=filtros_aplicados,
            resultados_encontrados=data.get('resultados_encontrados', 0),
            ip_address=data.get('ip_address') or None,
        )
        
        busqueda.full_clean()
        busqueda.save()
        
        # Retornar los datos de la búsqueda creada
        busqueda_dict = {
            'id': busqueda.id,
            'usuario_id': busqueda.usuario.id if busqueda.usuario else None,
            'usuario_nombre': busqueda.usuario.get_full_name() if busqueda.usuario and busqueda.usuario.get_full_name() else (busqueda.usuario.username if busqueda.usuario else 'Anónimo'),
            'termino_busqueda': busqueda.termino_busqueda,
            'filtros_aplicados': busqueda.filtros_aplicados,
            'resultados_encontrados': busqueda.resultados_encontrados,
            'ip_address': str(busqueda.ip_address) if busqueda.ip_address else '',
            'fecha': busqueda.fecha.isoformat() if busqueda.fecha else None,
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Búsqueda creada exitosamente',
            'data': busqueda_dict
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
            'error': f'Error al crear búsqueda: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def busqueda_detail(request, busqueda_id):
    """Obtiene los detalles de una búsqueda"""
    try:
        busqueda = get_object_or_404(Busqueda.objects.select_related('usuario'), id=busqueda_id)
        
        busqueda_dict = {
            'id': busqueda.id,
            'usuario_id': busqueda.usuario.id if busqueda.usuario else None,
            'usuario_nombre': busqueda.usuario.get_full_name() if busqueda.usuario and busqueda.usuario.get_full_name() else (busqueda.usuario.username if busqueda.usuario else 'Anónimo'),
            'termino_busqueda': busqueda.termino_busqueda,
            'filtros_aplicados': busqueda.filtros_aplicados,
            'resultados_encontrados': busqueda.resultados_encontrados,
            'ip_address': str(busqueda.ip_address) if busqueda.ip_address else '',
            'fecha': busqueda.fecha.isoformat() if busqueda.fecha else None,
        }
        
        return JsonResponse({
            'success': True,
            'data': busqueda_dict
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener búsqueda: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "PUT"])
def busqueda_update(request, busqueda_id):
    """Actualiza una búsqueda existente"""
    try:
        busqueda = get_object_or_404(Busqueda, id=busqueda_id)
        
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
        
        # Validar término de búsqueda
        termino_busqueda = data.get('termino_busqueda', '').strip()
        if not termino_busqueda:
            return JsonResponse({
                'success': False,
                'error': 'El término de búsqueda es obligatorio'
            }, status=400)
        
        # Procesar filtros_aplicados si es JSON
        filtros_aplicados = data.get('filtros_aplicados')
        if filtros_aplicados:
            if isinstance(filtros_aplicados, str):
                try:
                    filtros_aplicados = json.loads(filtros_aplicados)
                except json.JSONDecodeError:
                    return JsonResponse({
                        'success': False,
                        'error': 'filtros_aplicados debe ser un JSON válido'
                    }, status=400)
        else:
            filtros_aplicados = None
        
        # Actualizar campos
        busqueda.usuario_id = data.get('usuario_id') or None
        busqueda.termino_busqueda = termino_busqueda
        busqueda.filtros_aplicados = filtros_aplicados
        busqueda.resultados_encontrados = data.get('resultados_encontrados', busqueda.resultados_encontrados)
        busqueda.ip_address = data.get('ip_address') or None
        
        busqueda.full_clean()
        busqueda.save()
        
        # Retornar los datos actualizados
        busqueda_dict = {
            'id': busqueda.id,
            'usuario_id': busqueda.usuario.id if busqueda.usuario else None,
            'usuario_nombre': busqueda.usuario.get_full_name() if busqueda.usuario and busqueda.usuario.get_full_name() else (busqueda.usuario.username if busqueda.usuario else 'Anónimo'),
            'termino_busqueda': busqueda.termino_busqueda,
            'filtros_aplicados': busqueda.filtros_aplicados,
            'resultados_encontrados': busqueda.resultados_encontrados,
            'ip_address': str(busqueda.ip_address) if busqueda.ip_address else '',
            'fecha': busqueda.fecha.isoformat() if busqueda.fecha else None,
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Búsqueda actualizada exitosamente',
            'data': busqueda_dict
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
            'error': f'Error al actualizar búsqueda: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "DELETE"])
def busqueda_delete(request, busqueda_id):
    """Elimina una búsqueda"""
    try:
        busqueda = get_object_or_404(Busqueda, id=busqueda_id)
        
        # Manejar tanto POST con _method como DELETE directo
        if request.method == 'POST':
            data = json.loads(request.body) if request.body else {}
            if data.get('_method') != 'DELETE':
                return JsonResponse({
                    'success': False,
                    'error': 'Método no permitido'
                }, status=405)
        
        # Eliminar la búsqueda
        busqueda.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Búsqueda eliminada exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al eliminar búsqueda: {str(e)}'
        }, status=500)
