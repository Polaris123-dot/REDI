from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from datetime import datetime
import json
from .models import EsquemaMetadatos, CampoMetadatos, MetadatoDocumento
from repositorio.models import Documento


@login_required
@ensure_csrf_cookie
@require_http_methods(["GET"])
def index(request):
    """Vista principal de metadatos"""
    # Verificar permisos
    if not (request.user.has_perm('metadatos.view_esquametadatos') or 
            request.user.has_perm('metadatos.view_campometadatos') or
            request.user.has_perm('metadatos.view_metadatosdocumento') or
            request.user.is_superuser):
        messages.warning(request, 'No tienes permisos para acceder a metadatos.')
        return redirect('usuarios:panel')
    return render(request, 'metadatos/index.html')


# ============================================================================
# VISTAS AUXILIARES PARA SELECTS
# ============================================================================

@login_required
@require_http_methods(["GET"])
def esquemas_for_select(request):
    """Obtiene los esquemas de metadatos para usar en selects"""
    try:
        esquemas = EsquemaMetadatos.objects.all().order_by('nombre')
        esquemas_data = []
        
        for esquema in esquemas:
            esquemas_data.append({
                'id': esquema.id,
                'text': esquema.nombre,
                'prefijo': esquema.prefijo,
                'namespace': esquema.namespace,
            })
        
        return JsonResponse({
            'success': True,
            'data': esquemas_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener esquemas: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def campos_for_select(request):
    """Obtiene los campos de metadatos para usar en selects, opcionalmente filtrados por esquema"""
    try:
        esquema_id = request.GET.get('esquema_id', '')
        campos = CampoMetadatos.objects.select_related('esquema').all()
        
        if esquema_id:
            campos = campos.filter(esquema_id=esquema_id)
        
        campos = campos.order_by('esquema__nombre', 'nombre')
        campos_data = []
        
        for campo in campos:
            campos_data.append({
                'id': campo.id,
                'text': f"{campo.esquema.nombre} - {campo.etiqueta}",
                'nombre': campo.nombre,
                'etiqueta': campo.etiqueta,
                'tipo_dato': campo.tipo_dato,
                'esquema_id': campo.esquema.id,
                'esquema_nombre': campo.esquema.nombre,
            })
        
        return JsonResponse({
            'success': True,
            'data': campos_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener campos: {str(e)}'
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


# ============================================================================
# VISTAS PARA ESQUEMAS DE METADATOS
# ============================================================================

@login_required
@require_http_methods(["GET"])
def esquemas_list(request):
    """Lista todos los esquemas de metadatos en formato JSON"""
    esquemas = EsquemaMetadatos.objects.all()
    esquemas_data = []
    
    for esquema in esquemas:
        esquema_dict = {
            'id': esquema.id,
            'nombre': esquema.nombre,
            'prefijo': esquema.prefijo,
            'namespace': esquema.namespace,
            'descripcion': esquema.descripcion or '',
            'version': esquema.version or '',
            'campos_count': esquema.campos.count(),
        }
        esquemas_data.append(esquema_dict)
    
    return JsonResponse({
        'success': True,
        'data': esquemas_data,
        'total': len(esquemas_data)
    })


@login_required
@require_http_methods(["POST"])
def esquema_create(request):
    """Crea un nuevo esquema de metadatos"""
    try:
        data = json.loads(request.body)
        
        # Validar campos requeridos
        nombre = data.get('nombre', '').strip()
        if not nombre:
            return JsonResponse({
                'success': False,
                'error': 'El nombre es obligatorio'
            }, status=400)
        
        prefijo = data.get('prefijo', '').strip()
        if not prefijo:
            return JsonResponse({
                'success': False,
                'error': 'El prefijo es obligatorio'
            }, status=400)
        
        namespace = data.get('namespace', '').strip()
        if not namespace:
            return JsonResponse({
                'success': False,
                'error': 'El namespace es obligatorio'
            }, status=400)
        
        # Verificar que el nombre no exista
        if EsquemaMetadatos.objects.filter(nombre=nombre).exists():
            return JsonResponse({
                'success': False,
                'error': 'Ya existe un esquema con este nombre'
            }, status=400)
        
        # Verificar que el prefijo no exista
        if EsquemaMetadatos.objects.filter(prefijo=prefijo).exists():
            return JsonResponse({
                'success': False,
                'error': 'Ya existe un esquema con este prefijo'
            }, status=400)
        
        # Crear el esquema
        esquema = EsquemaMetadatos(
            nombre=nombre,
            prefijo=prefijo,
            namespace=namespace,
            descripcion=data.get('descripcion', '').strip() or None,
            version=data.get('version', '').strip() or None,
        )
        
        esquema.full_clean()
        esquema.save()
        
        # Retornar los datos del esquema creado
        esquema_dict = {
            'id': esquema.id,
            'nombre': esquema.nombre,
            'prefijo': esquema.prefijo,
            'namespace': esquema.namespace,
            'descripcion': esquema.descripcion or '',
            'version': esquema.version or '',
            'campos_count': esquema.campos.count(),
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Esquema de metadatos creado exitosamente',
            'data': esquema_dict
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
            'error': f'Error al crear esquema de metadatos: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def esquema_detail(request, esquema_id):
    """Obtiene los detalles de un esquema de metadatos"""
    try:
        esquema = get_object_or_404(EsquemaMetadatos, id=esquema_id)
        
        esquema_dict = {
            'id': esquema.id,
            'nombre': esquema.nombre,
            'prefijo': esquema.prefijo,
            'namespace': esquema.namespace,
            'descripcion': esquema.descripcion or '',
            'version': esquema.version or '',
            'campos_count': esquema.campos.count(),
        }
        
        return JsonResponse({
            'success': True,
            'data': esquema_dict
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener esquema de metadatos: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "PUT"])
def esquema_update(request, esquema_id):
    """Actualiza un esquema de metadatos existente"""
    try:
        esquema = get_object_or_404(EsquemaMetadatos, id=esquema_id)
        
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
        
        # Validar nombre
        nombre = data.get('nombre', '').strip()
        if not nombre:
            return JsonResponse({
                'success': False,
                'error': 'El nombre es obligatorio'
            }, status=400)
        
        # Verificar que el nombre no exista en otro esquema
        if EsquemaMetadatos.objects.filter(nombre=nombre).exclude(id=esquema_id).exists():
            return JsonResponse({
                'success': False,
                'error': 'Ya existe otro esquema con este nombre'
            }, status=400)
        
        # Validar prefijo
        prefijo = data.get('prefijo', '').strip()
        if not prefijo:
            return JsonResponse({
                'success': False,
                'error': 'El prefijo es obligatorio'
            }, status=400)
        
        # Verificar que el prefijo no exista en otro esquema
        if EsquemaMetadatos.objects.filter(prefijo=prefijo).exclude(id=esquema_id).exists():
            return JsonResponse({
                'success': False,
                'error': 'Ya existe otro esquema con este prefijo'
            }, status=400)
        
        # Validar namespace
        namespace = data.get('namespace', '').strip()
        if not namespace:
            return JsonResponse({
                'success': False,
                'error': 'El namespace es obligatorio'
            }, status=400)
        
        # Actualizar campos
        esquema.nombre = nombre
        esquema.prefijo = prefijo
        esquema.namespace = namespace
        esquema.descripcion = data.get('descripcion', '').strip() or None
        esquema.version = data.get('version', '').strip() or None
        
        esquema.full_clean()
        esquema.save()
        
        # Retornar los datos actualizados
        esquema_dict = {
            'id': esquema.id,
            'nombre': esquema.nombre,
            'prefijo': esquema.prefijo,
            'namespace': esquema.namespace,
            'descripcion': esquema.descripcion or '',
            'version': esquema.version or '',
            'campos_count': esquema.campos.count(),
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Esquema de metadatos actualizado exitosamente',
            'data': esquema_dict
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
            'error': f'Error al actualizar esquema de metadatos: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "DELETE"])
def esquema_delete(request, esquema_id):
    """Elimina un esquema de metadatos"""
    try:
        esquema = get_object_or_404(EsquemaMetadatos, id=esquema_id)
        
        # Manejar tanto POST con _method como DELETE directo
        if request.method == 'POST':
            data = json.loads(request.body) if request.body else {}
            if data.get('_method') != 'DELETE':
                return JsonResponse({
                    'success': False,
                    'error': 'Método no permitido'
                }, status=405)
        
        # Verificar si tiene campos asociados
        if esquema.campos.exists():
            return JsonResponse({
                'success': False,
                'error': f'No se puede eliminar este esquema porque tiene {esquema.campos.count()} campo(s) asociado(s)'
            }, status=400)
        
        # Eliminar el esquema
        esquema_nombre = esquema.nombre
        esquema.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Esquema de metadatos "{esquema_nombre}" eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al eliminar esquema de metadatos: {str(e)}'
        }, status=500)


# ============================================================================
# VISTAS PARA CAMPOS DE METADATOS
# ============================================================================

@login_required
@require_http_methods(["GET"])
def campos_list(request):
    """Lista todos los campos de metadatos en formato JSON"""
    campos = CampoMetadatos.objects.select_related('esquema').all()
    campos_data = []
    
    for campo in campos:
        campo_dict = {
            'id': campo.id,
            'esquema_id': campo.esquema.id,
            'esquema_nombre': campo.esquema.nombre,
            'nombre': campo.nombre,
            'etiqueta': campo.etiqueta,
            'tipo_dato': campo.tipo_dato,
            'tipo_dato_display': campo.get_tipo_dato_display(),
            'es_obligatorio': campo.es_obligatorio,
            'es_repetible': campo.es_repetible,
            'valores_posibles': campo.valores_posibles,
            'descripcion': campo.descripcion or '',
            'valores_count': campo.valores.count(),
        }
        campos_data.append(campo_dict)
    
    return JsonResponse({
        'success': True,
        'data': campos_data,
        'total': len(campos_data)
    })


@login_required
@require_http_methods(["POST"])
def campo_create(request):
    """Crea un nuevo campo de metadatos"""
    try:
        data = json.loads(request.body)
        
        # Validar campos requeridos
        esquema_id = data.get('esquema_id')
        if not esquema_id:
            return JsonResponse({
                'success': False,
                'error': 'El esquema es obligatorio'
            }, status=400)
        
        esquema = get_object_or_404(EsquemaMetadatos, id=esquema_id)
        
        nombre = data.get('nombre', '').strip()
        if not nombre:
            return JsonResponse({
                'success': False,
                'error': 'El nombre es obligatorio'
            }, status=400)
        
        etiqueta = data.get('etiqueta', '').strip()
        if not etiqueta:
            return JsonResponse({
                'success': False,
                'error': 'La etiqueta es obligatoria'
            }, status=400)
        
        # Verificar que el nombre no exista en este esquema
        if CampoMetadatos.objects.filter(esquema=esquema, nombre=nombre).exists():
            return JsonResponse({
                'success': False,
                'error': 'Ya existe un campo con este nombre en este esquema'
            }, status=400)
        
        # Procesar valores_posibles si es JSON
        valores_posibles = data.get('valores_posibles')
        if valores_posibles:
            if isinstance(valores_posibles, str):
                try:
                    valores_posibles = json.loads(valores_posibles)
                except json.JSONDecodeError:
                    return JsonResponse({
                        'success': False,
                        'error': 'valores_posibles debe ser un JSON válido'
                    }, status=400)
        else:
            valores_posibles = None
        
        # Crear el campo
        campo = CampoMetadatos(
            esquema=esquema,
            nombre=nombre,
            etiqueta=etiqueta,
            tipo_dato=data.get('tipo_dato', 'texto'),
            es_obligatorio=data.get('es_obligatorio', False),
            es_repetible=data.get('es_repetible', False),
            valores_posibles=valores_posibles,
            descripcion=data.get('descripcion', '').strip() or None,
        )
        
        campo.full_clean()
        campo.save()
        
        # Retornar los datos del campo creado
        campo_dict = {
            'id': campo.id,
            'esquema_id': campo.esquema.id,
            'esquema_nombre': campo.esquema.nombre,
            'nombre': campo.nombre,
            'etiqueta': campo.etiqueta,
            'tipo_dato': campo.tipo_dato,
            'tipo_dato_display': campo.get_tipo_dato_display(),
            'es_obligatorio': campo.es_obligatorio,
            'es_repetible': campo.es_repetible,
            'valores_posibles': campo.valores_posibles,
            'descripcion': campo.descripcion or '',
            'valores_count': campo.valores.count(),
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Campo de metadatos creado exitosamente',
            'data': campo_dict
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
            'error': f'Error al crear campo de metadatos: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def campo_detail(request, campo_id):
    """Obtiene los detalles de un campo de metadatos"""
    try:
        campo = get_object_or_404(CampoMetadatos.objects.select_related('esquema'), id=campo_id)
        
        campo_dict = {
            'id': campo.id,
            'esquema_id': campo.esquema.id,
            'esquema_nombre': campo.esquema.nombre,
            'nombre': campo.nombre,
            'etiqueta': campo.etiqueta,
            'tipo_dato': campo.tipo_dato,
            'tipo_dato_display': campo.get_tipo_dato_display(),
            'es_obligatorio': campo.es_obligatorio,
            'es_repetible': campo.es_repetible,
            'valores_posibles': campo.valores_posibles,
            'descripcion': campo.descripcion or '',
            'valores_count': campo.valores.count(),
        }
        
        return JsonResponse({
            'success': True,
            'data': campo_dict
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener campo de metadatos: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "PUT"])
def campo_update(request, campo_id):
    """Actualiza un campo de metadatos existente"""
    try:
        campo = get_object_or_404(CampoMetadatos, id=campo_id)
        
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
        
        # Validar etiqueta
        etiqueta = data.get('etiqueta', '').strip()
        if not etiqueta:
            return JsonResponse({
                'success': False,
                'error': 'La etiqueta es obligatoria'
            }, status=400)
        
        # Validar nombre si se cambia
        nombre = data.get('nombre', '').strip()
        if nombre and nombre != campo.nombre:
            # Verificar que el nombre no exista en este esquema
            if CampoMetadatos.objects.filter(esquema=campo.esquema, nombre=nombre).exclude(id=campo_id).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Ya existe otro campo con este nombre en este esquema'
                }, status=400)
            campo.nombre = nombre
        
        # Procesar valores_posibles si es JSON
        valores_posibles = data.get('valores_posibles')
        if valores_posibles:
            if isinstance(valores_posibles, str):
                try:
                    valores_posibles = json.loads(valores_posibles)
                except json.JSONDecodeError:
                    return JsonResponse({
                        'success': False,
                        'error': 'valores_posibles debe ser un JSON válido'
                    }, status=400)
        else:
            valores_posibles = None
        
        # Actualizar campos
        campo.etiqueta = etiqueta
        if 'tipo_dato' in data:
            campo.tipo_dato = data.get('tipo_dato')
        campo.es_obligatorio = data.get('es_obligatorio', campo.es_obligatorio)
        campo.es_repetible = data.get('es_repetible', campo.es_repetible)
        campo.valores_posibles = valores_posibles
        campo.descripcion = data.get('descripcion', '').strip() or None
        
        campo.full_clean()
        campo.save()
        
        # Retornar los datos actualizados
        campo_dict = {
            'id': campo.id,
            'esquema_id': campo.esquema.id,
            'esquema_nombre': campo.esquema.nombre,
            'nombre': campo.nombre,
            'etiqueta': campo.etiqueta,
            'tipo_dato': campo.tipo_dato,
            'tipo_dato_display': campo.get_tipo_dato_display(),
            'es_obligatorio': campo.es_obligatorio,
            'es_repetible': campo.es_repetible,
            'valores_posibles': campo.valores_posibles,
            'descripcion': campo.descripcion or '',
            'valores_count': campo.valores.count(),
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Campo de metadatos actualizado exitosamente',
            'data': campo_dict
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
            'error': f'Error al actualizar campo de metadatos: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "DELETE"])
def campo_delete(request, campo_id):
    """Elimina un campo de metadatos"""
    try:
        campo = get_object_or_404(CampoMetadatos, id=campo_id)
        
        # Manejar tanto POST con _method como DELETE directo
        if request.method == 'POST':
            data = json.loads(request.body) if request.body else {}
            if data.get('_method') != 'DELETE':
                return JsonResponse({
                    'success': False,
                    'error': 'Método no permitido'
                }, status=405)
        
        # Verificar si tiene valores asociados
        if campo.valores.exists():
            return JsonResponse({
                'success': False,
                'error': f'No se puede eliminar este campo porque tiene {campo.valores.count()} valor(es) asociado(s)'
            }, status=400)
        
        # Eliminar el campo
        campo_nombre = campo.etiqueta
        campo.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Campo de metadatos "{campo_nombre}" eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al eliminar campo de metadatos: {str(e)}'
        }, status=500)


# ============================================================================
# VISTAS PARA METADATOS DE DOCUMENTOS
# ============================================================================

@login_required
@require_http_methods(["GET"])
def metadatos_documentos_list(request):
    """Lista todos los metadatos de documentos en formato JSON"""
    metadatos = MetadatoDocumento.objects.select_related('documento', 'campo_metadato', 'campo_metadato__esquema').all()
    metadatos_data = []
    
    for metadato in metadatos:
        # Obtener el valor según el tipo de dato
        valor = metadato.get_valor()
        valor_str = ''
        if valor is not None:
            if isinstance(valor, (dict, list)):
                valor_str = json.dumps(valor)
            else:
                valor_str = str(valor)
        
        metadato_dict = {
            'id': metadato.id,
            'documento_id': metadato.documento.id,
            'documento_titulo': metadato.documento.get_titulo() if hasattr(metadato.documento, 'get_titulo') else (metadato.documento.titulo or f'Documento #{metadato.documento.id}'),
            'campo_metadato_id': metadato.campo_metadato.id,
            'campo_metadato_nombre': metadato.campo_metadato.etiqueta,
            'campo_metadato_esquema': metadato.campo_metadato.esquema.nombre,
            'tipo_dato': metadato.campo_metadato.tipo_dato,
            'valor': valor_str,
            'idioma': metadato.idioma or '',
            'orden': metadato.orden,
        }
        metadatos_data.append(metadato_dict)
    
    return JsonResponse({
        'success': True,
        'data': metadatos_data,
        'total': len(metadatos_data)
    })


@login_required
@require_http_methods(["POST"])
def metadato_documento_create(request):
    """Crea un nuevo metadato de documento"""
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
        
        campo_metadato_id = data.get('campo_metadato_id')
        if not campo_metadato_id:
            return JsonResponse({
                'success': False,
                'error': 'El campo de metadatos es obligatorio'
            }, status=400)
        
        campo_metadato = get_object_or_404(CampoMetadatos, id=campo_metadato_id)
        
        # Obtener el valor según el tipo de dato
        tipo_dato = campo_metadato.tipo_dato
        valor_texto = None
        valor_numero = None
        valor_fecha = None
        valor_booleano = None
        valor_json = None
        
        if tipo_dato == 'texto' or tipo_dato == 'lista':
            valor_texto = data.get('valor', '').strip() or None
        elif tipo_dato == 'numero':
            valor = data.get('valor')
            if valor:
                try:
                    valor_numero = float(valor)
                except (ValueError, TypeError):
                    return JsonResponse({
                        'success': False,
                        'error': 'El valor debe ser un número válido'
                    }, status=400)
        elif tipo_dato == 'fecha':
            valor = data.get('valor', '').strip()
            if valor:
                try:
                    from django.utils.dateparse import parse_date
                    valor_fecha = parse_date(valor)
                    if not valor_fecha:
                        return JsonResponse({
                            'success': False,
                            'error': 'El valor debe ser una fecha válida (formato: YYYY-MM-DD)'
                        }, status=400)
                except (ValueError, TypeError):
                    return JsonResponse({
                        'success': False,
                        'error': 'El valor debe ser una fecha válida (formato: YYYY-MM-DD)'
                    }, status=400)
        elif tipo_dato == 'booleano':
            valor = data.get('valor')
            if valor is not None:
                if isinstance(valor, bool):
                    valor_booleano = valor
                elif isinstance(valor, str):
                    valor_booleano = valor.lower() in ('true', '1', 'yes', 'si', 'sí')
                else:
                    valor_booleano = bool(valor)
        elif tipo_dato == 'json':
            valor = data.get('valor')
            if valor:
                if isinstance(valor, str):
                    try:
                        valor_json = json.loads(valor)
                    except json.JSONDecodeError:
                        return JsonResponse({
                            'success': False,
                            'error': 'El valor debe ser un JSON válido'
                        }, status=400)
                else:
                    valor_json = valor
        
        # Validar si es obligatorio
        if campo_metadato.es_obligatorio:
            valor_provisto = valor_texto or valor_numero is not None or valor_fecha is not None or valor_booleano is not None or valor_json is not None
            if not valor_provisto:
                return JsonResponse({
                    'success': False,
                    'error': f'El campo "{campo_metadato.etiqueta}" es obligatorio'
                }, status=400)
        
        # Crear el metadato
        metadato = MetadatoDocumento(
            documento=documento,
            campo_metadato=campo_metadato,
            valor_texto=valor_texto,
            valor_numero=valor_numero,
            valor_fecha=valor_fecha,
            valor_booleano=valor_booleano,
            valor_json=valor_json,
            idioma=data.get('idioma', '').strip() or None,
            orden=data.get('orden', 0),
        )
        
        metadato.full_clean()
        metadato.save()
        
        # Retornar los datos del metadato creado
        valor = metadato.get_valor()
        valor_str = ''
        if valor is not None:
            if isinstance(valor, (dict, list)):
                valor_str = json.dumps(valor)
            else:
                valor_str = str(valor)
        
        metadato_dict = {
            'id': metadato.id,
            'documento_id': metadato.documento.id,
            'documento_titulo': metadato.documento.get_titulo() if hasattr(metadato.documento, 'get_titulo') else (metadato.documento.titulo or f'Documento #{metadato.documento.id}'),
            'campo_metadato_id': metadato.campo_metadato.id,
            'campo_metadato_nombre': metadato.campo_metadato.etiqueta,
            'campo_metadato_esquema': metadato.campo_metadato.esquema.nombre,
            'tipo_dato': metadato.campo_metadato.tipo_dato,
            'valor': valor_str,
            'idioma': metadato.idioma or '',
            'orden': metadato.orden,
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Metadato de documento creado exitosamente',
            'data': metadato_dict
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
            'error': f'Error al crear metadato de documento: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def metadato_documento_detail(request, metadato_id):
    """Obtiene los detalles de un metadato de documento"""
    try:
        metadato = get_object_or_404(
            MetadatoDocumento.objects.select_related('documento', 'campo_metadato', 'campo_metadato__esquema'),
            id=metadato_id
        )
        
        # Obtener el valor según el tipo de dato
        valor = metadato.get_valor()
        valor_str = ''
        if valor is not None:
            if isinstance(valor, (dict, list)):
                valor_str = json.dumps(valor)
            elif isinstance(valor, (datetime,)):
                valor_str = valor.isoformat()
            else:
                valor_str = str(valor)
        
        metadato_dict = {
            'id': metadato.id,
            'documento_id': metadato.documento.id,
            'documento_titulo': metadato.documento.get_titulo() if hasattr(metadato.documento, 'get_titulo') else (metadato.documento.titulo or f'Documento #{metadato.documento.id}'),
            'campo_metadato_id': metadato.campo_metadato.id,
            'campo_metadato_nombre': metadato.campo_metadato.etiqueta,
            'campo_metadato_esquema': metadato.campo_metadato.esquema.nombre,
            'tipo_dato': metadato.campo_metadato.tipo_dato,
            'valor': valor_str,
            'idioma': metadato.idioma or '',
            'orden': metadato.orden,
        }
        
        return JsonResponse({
            'success': True,
            'data': metadato_dict
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener metadato de documento: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "PUT"])
def metadato_documento_update(request, metadato_id):
    """Actualiza un metadato de documento existente"""
    try:
        metadato = get_object_or_404(MetadatoDocumento, id=metadato_id)
        
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
        
        # Obtener el tipo de dato del campo
        tipo_dato = metadato.campo_metadato.tipo_dato
        
        # Limpiar todos los valores primero
        metadato.valor_texto = None
        metadato.valor_numero = None
        metadato.valor_fecha = None
        metadato.valor_booleano = None
        metadato.valor_json = None
        
        # Establecer el valor según el tipo de dato
        if tipo_dato == 'texto' or tipo_dato == 'lista':
            metadato.valor_texto = data.get('valor', '').strip() or None
        elif tipo_dato == 'numero':
            valor = data.get('valor')
            if valor:
                try:
                    metadato.valor_numero = float(valor)
                except (ValueError, TypeError):
                    return JsonResponse({
                        'success': False,
                        'error': 'El valor debe ser un número válido'
                    }, status=400)
        elif tipo_dato == 'fecha':
            valor = data.get('valor', '').strip()
            if valor:
                try:
                    from django.utils.dateparse import parse_date
                    metadato.valor_fecha = parse_date(valor)
                    if not metadato.valor_fecha:
                        return JsonResponse({
                            'success': False,
                            'error': 'El valor debe ser una fecha válida (formato: YYYY-MM-DD)'
                        }, status=400)
                except (ValueError, TypeError):
                    return JsonResponse({
                        'success': False,
                        'error': 'El valor debe ser una fecha válida (formato: YYYY-MM-DD)'
                    }, status=400)
        elif tipo_dato == 'booleano':
            valor = data.get('valor')
            if valor is not None:
                if isinstance(valor, bool):
                    metadato.valor_booleano = valor
                elif isinstance(valor, str):
                    metadato.valor_booleano = valor.lower() in ('true', '1', 'yes', 'si', 'sí')
                else:
                    metadato.valor_booleano = bool(valor)
        elif tipo_dato == 'json':
            valor = data.get('valor')
            if valor:
                if isinstance(valor, str):
                    try:
                        metadato.valor_json = json.loads(valor)
                    except json.JSONDecodeError:
                        return JsonResponse({
                            'success': False,
                            'error': 'El valor debe ser un JSON válido'
                        }, status=400)
                else:
                    metadato.valor_json = valor
        
        # Validar si es obligatorio
        if metadato.campo_metadato.es_obligatorio:
            valor_provisto = (metadato.valor_texto or 
                             metadato.valor_numero is not None or 
                             metadato.valor_fecha is not None or 
                             metadato.valor_booleano is not None or 
                             metadato.valor_json is not None)
            if not valor_provisto:
                return JsonResponse({
                    'success': False,
                    'error': f'El campo "{metadato.campo_metadato.etiqueta}" es obligatorio'
                }, status=400)
        
        # Actualizar otros campos
        metadato.idioma = data.get('idioma', '').strip() or None
        metadato.orden = data.get('orden', metadato.orden)
        
        metadato.full_clean()
        metadato.save()
        
        # Retornar los datos actualizados
        valor = metadato.get_valor()
        valor_str = ''
        if valor is not None:
            if isinstance(valor, (dict, list)):
                valor_str = json.dumps(valor)
            else:
                valor_str = str(valor)
        
        metadato_dict = {
            'id': metadato.id,
            'documento_id': metadato.documento.id,
            'documento_titulo': metadato.documento.get_titulo() if hasattr(metadato.documento, 'get_titulo') else (metadato.documento.titulo or f'Documento #{metadato.documento.id}'),
            'campo_metadato_id': metadato.campo_metadato.id,
            'campo_metadato_nombre': metadato.campo_metadato.etiqueta,
            'campo_metadato_esquema': metadato.campo_metadato.esquema.nombre,
            'tipo_dato': metadato.campo_metadato.tipo_dato,
            'valor': valor_str,
            'idioma': metadato.idioma or '',
            'orden': metadato.orden,
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Metadato de documento actualizado exitosamente',
            'data': metadato_dict
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
            'error': f'Error al actualizar metadato de documento: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "DELETE"])
def metadato_documento_delete(request, metadato_id):
    """Elimina un metadato de documento"""
    try:
        metadato = get_object_or_404(MetadatoDocumento, id=metadato_id)
        
        # Manejar tanto POST con _method como DELETE directo
        if request.method == 'POST':
            data = json.loads(request.body) if request.body else {}
            if data.get('_method') != 'DELETE':
                return JsonResponse({
                    'success': False,
                    'error': 'Método no permitido'
                }, status=405)
        
        # Eliminar el metadato
        metadato.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Metadato de documento eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al eliminar metadato de documento: {str(e)}'
        }, status=500)
