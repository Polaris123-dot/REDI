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
            'fecha_creacion': tipo.fecha_creacion.isoformat() if tipo.fecha_creacion else None,
            'campos_count': tipo.campos.count(),
            'proyectos_count': tipo.proyectos.count(),
        }
        tipos_data.append(tipo_dict)
    
    return JsonResponse({
        'success': True,
        'data': tipos_data,
        'total': len(tipos_data)
    })


@login_required
@require_http_methods(["POST"])
def tipo_proyecto_create(request):
    """Crea un nuevo tipo de proyecto"""
    try:
        data = json.loads(request.body)
        
        # Validar campos requeridos
        nombre = data.get('nombre', '').strip()
        if not nombre:
            return JsonResponse({
                'success': False,
                'error': 'El nombre es obligatorio'
            }, status=400)
        
        # Validar que el nombre no exista
        if TipoProyecto.objects.filter(nombre=nombre).exists():
            return JsonResponse({
                'success': False,
                'error': 'Ya existe un tipo de proyecto con este nombre'
            }, status=400)
        
        # Generar slug desde el nombre
        slug = slugify(nombre)
        
        # Verificar que el slug no esté vacío
        if not slug:
            return JsonResponse({
                'success': False,
                'error': 'El nombre no puede generar un slug válido'
            }, status=400)
        
        # Validar que el slug no exista
        if TipoProyecto.objects.filter(slug=slug).exists():
            return JsonResponse({
                'success': False,
                'error': 'Ya existe un tipo de proyecto con un nombre similar'
            }, status=400)
        
        # Crear el tipo de proyecto
        tipo = TipoProyecto(
            nombre=nombre,
            slug=slug,
            descripcion=data.get('descripcion', '').strip() or None,
            icono=data.get('icono', '').strip() or None,
            color=data.get('color', '').strip() or None,
            plantilla_vista=data.get('plantilla_vista', '').strip() or None,
            es_activo=data.get('es_activo', True),
            orden=data.get('orden', 0)
        )
        
        # Validar antes de guardar
        tipo.full_clean()
        tipo.save()
        
        # Retornar los datos del tipo creado
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
            'fecha_creacion': tipo.fecha_creacion.isoformat() if tipo.fecha_creacion else None,
            'campos_count': 0,
            'proyectos_count': 0,
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Tipo de proyecto creado exitosamente',
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
            'error': f'Error al crear tipo de proyecto: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def tipo_proyecto_detail(request, tipo_proyecto_id):
    """Obtiene los detalles de un tipo de proyecto"""
    try:
        tipo = get_object_or_404(TipoProyecto, id=tipo_proyecto_id)
        
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
            'fecha_creacion': tipo.fecha_creacion.isoformat() if tipo.fecha_creacion else None,
            'campos_count': tipo.campos.count(),
            'proyectos_count': tipo.proyectos.count(),
        }
        
        return JsonResponse({
            'success': True,
            'data': tipo_dict
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener tipo de proyecto: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "PUT"])
def tipo_proyecto_update(request, tipo_proyecto_id):
    """Actualiza un tipo de proyecto"""
    try:
        tipo = get_object_or_404(TipoProyecto, id=tipo_proyecto_id)
        
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
        
        # Validar que el nombre no exista en otro tipo
        if TipoProyecto.objects.filter(nombre=nombre).exclude(id=tipo_proyecto_id).exists():
            return JsonResponse({
                'success': False,
                'error': 'Ya existe otro tipo de proyecto con este nombre'
            }, status=400)
        
        # Generar slug desde el nombre si cambió
        nuevo_slug = slugify(nombre)
        
        # Verificar que el slug no esté vacío
        if not nuevo_slug:
            return JsonResponse({
                'success': False,
                'error': 'El nombre no puede generar un slug válido'
            }, status=400)
        
        # Si el slug cambió, validar que no exista
        if nuevo_slug != tipo.slug and TipoProyecto.objects.filter(slug=nuevo_slug).exists():
            return JsonResponse({
                'success': False,
                'error': 'Ya existe otro tipo de proyecto con un nombre similar'
            }, status=400)
        
        # Actualizar los campos
        tipo.nombre = nombre
        tipo.slug = nuevo_slug
        tipo.descripcion = data.get('descripcion', '').strip() or None
        tipo.icono = data.get('icono', '').strip() or None
        tipo.color = data.get('color', '').strip() or None
        tipo.plantilla_vista = data.get('plantilla_vista', '').strip() or None
        tipo.es_activo = data.get('es_activo', True)
        tipo.orden = data.get('orden', 0)
        
        # Validar antes de guardar
        tipo.full_clean()
        tipo.save()
        
        # Retornar los datos actualizados
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
            'fecha_creacion': tipo.fecha_creacion.isoformat() if tipo.fecha_creacion else None,
            'campos_count': tipo.campos.count(),
            'proyectos_count': tipo.proyectos.count(),
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Tipo de proyecto actualizado exitosamente',
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
            'error': f'Error al actualizar tipo de proyecto: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "DELETE"])
def tipo_proyecto_delete(request, tipo_proyecto_id):
    """Elimina un tipo de proyecto"""
    try:
        tipo = get_object_or_404(TipoProyecto, id=tipo_proyecto_id)
        
        # Manejar tanto POST con _method como DELETE directo
        if request.method == 'POST':
            data = json.loads(request.body) if request.body else {}
            if data.get('_method') != 'DELETE':
                return JsonResponse({
                    'success': False,
                    'error': 'Método no permitido'
                }, status=405)
        
        # Verificar si tiene proyectos asociados
        if tipo.proyectos.exists():
            return JsonResponse({
                'success': False,
                'error': 'No se puede eliminar este tipo de proyecto porque tiene proyectos asociados'
            }, status=400)
        
        # Eliminar el tipo
        tipo_nombre = tipo.nombre
        tipo.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Tipo de proyecto "{tipo_nombre}" eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al eliminar tipo de proyecto: {str(e)}'
        }, status=500)


# ============================================================================
# VISTAS PARA CAMPOS DE TIPO DE PROYECTO
# ============================================================================

@login_required
@require_http_methods(["GET"])
def campos_tipo_proyecto_list(request):
    """Lista todos los campos de tipo de proyecto en formato JSON"""
    campos = CampoTipoProyecto.objects.select_related('tipo_proyecto').all()
    campos_data = []
    
    for campo in campos:
        campo_dict = {
            'id': campo.id,
            'tipo_proyecto_id': campo.tipo_proyecto.id,
            'tipo_proyecto_nombre': campo.tipo_proyecto.nombre,
            'nombre': campo.nombre,
            'slug': campo.slug,
            'etiqueta': campo.etiqueta,
            'descripcion': campo.descripcion or '',
            'tipo_dato': campo.tipo_dato,
            'tipo_dato_display': campo.get_tipo_dato_display(),
            'es_obligatorio': campo.es_obligatorio,
            'es_repetible': campo.es_repetible,
            'es_buscable': campo.es_buscable,
            'es_indexable': campo.es_indexable,
            'orden': campo.orden,
            'valores_posibles': campo.valores_posibles,
            'validador': campo.validador or '',
            'valor_por_defecto': campo.valor_por_defecto or '',
            'ayuda': campo.ayuda or '',
            'categoria': campo.categoria or '',
            'fecha_creacion': campo.fecha_creacion.isoformat() if campo.fecha_creacion else None,
        }
        campos_data.append(campo_dict)
    
    return JsonResponse({
        'success': True,
        'data': campos_data,
        'total': len(campos_data)
    })


@login_required
@require_http_methods(["POST"])
def campo_tipo_proyecto_create(request):
    """Crea un nuevo campo de tipo de proyecto"""
    try:
        data = json.loads(request.body)
        
        # Validar campos requeridos
        tipo_proyecto_id = data.get('tipo_proyecto_id')
        if not tipo_proyecto_id:
            return JsonResponse({
                'success': False,
                'error': 'El tipo de proyecto es obligatorio'
            }, status=400)
        
        tipo_proyecto = get_object_or_404(TipoProyecto, id=tipo_proyecto_id)
        
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
        
        # Validar que el slug no exista para este tipo de proyecto
        slug = data.get('slug', '').strip()
        if not slug:
            # Generar slug desde el nombre si no se proporciona
            slug = slugify(nombre)
        
        if CampoTipoProyecto.objects.filter(tipo_proyecto=tipo_proyecto, slug=slug).exists():
            return JsonResponse({
                'success': False,
                'error': 'Ya existe un campo con este nombre/slug para este tipo de proyecto'
            }, status=400)
        
        # Procesar valores_posibles si es JSON string
        valores_posibles = data.get('valores_posibles')
        if valores_posibles and isinstance(valores_posibles, str):
            try:
                valores_posibles = json.loads(valores_posibles)
            except:
                # Si no es JSON válido, tratarlo como lista separada por comas
                valores_posibles = [v.strip() for v in valores_posibles.split(',') if v.strip()]
        
        # Crear el campo
        campo = CampoTipoProyecto(
            tipo_proyecto=tipo_proyecto,
            nombre=nombre,
            slug=slug,
            etiqueta=etiqueta,
            descripcion=data.get('descripcion', '').strip() or None,
            tipo_dato=data.get('tipo_dato', 'texto'),
            es_obligatorio=data.get('es_obligatorio', False),
            es_repetible=data.get('es_repetible', False),
            es_buscable=data.get('es_buscable', True),
            es_indexable=data.get('es_indexable', True),
            orden=data.get('orden', 0),
            valores_posibles=valores_posibles,
            validador=data.get('validador', '').strip() or None,
            valor_por_defecto=data.get('valor_por_defecto', '').strip() or None,
            ayuda=data.get('ayuda', '').strip() or None,
            categoria=data.get('categoria', '').strip() or None,
        )
        
        # Validar antes de guardar
        campo.full_clean()
        campo.save()
        
        # Retornar los datos del campo creado
        campo_dict = {
            'id': campo.id,
            'tipo_proyecto_id': campo.tipo_proyecto.id,
            'tipo_proyecto_nombre': campo.tipo_proyecto.nombre,
            'nombre': campo.nombre,
            'slug': campo.slug,
            'etiqueta': campo.etiqueta,
            'descripcion': campo.descripcion or '',
            'tipo_dato': campo.tipo_dato,
            'tipo_dato_display': campo.get_tipo_dato_display(),
            'es_obligatorio': campo.es_obligatorio,
            'es_repetible': campo.es_repetible,
            'es_buscable': campo.es_buscable,
            'es_indexable': campo.es_indexable,
            'orden': campo.orden,
            'valores_posibles': campo.valores_posibles,
            'validador': campo.validador or '',
            'valor_por_defecto': campo.valor_por_defecto or '',
            'ayuda': campo.ayuda or '',
            'categoria': campo.categoria or '',
            'fecha_creacion': campo.fecha_creacion.isoformat() if campo.fecha_creacion else None,
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Campo de tipo de proyecto creado exitosamente',
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
            'error': f'Error al crear campo de tipo de proyecto: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def campo_tipo_proyecto_detail(request, campo_id):
    """Obtiene los detalles de un campo de tipo de proyecto"""
    try:
        campo = get_object_or_404(CampoTipoProyecto, id=campo_id)
        
        campo_dict = {
            'id': campo.id,
            'tipo_proyecto_id': campo.tipo_proyecto.id,
            'tipo_proyecto_nombre': campo.tipo_proyecto.nombre,
            'nombre': campo.nombre,
            'slug': campo.slug,
            'etiqueta': campo.etiqueta,
            'descripcion': campo.descripcion or '',
            'tipo_dato': campo.tipo_dato,
            'tipo_dato_display': campo.get_tipo_dato_display(),
            'es_obligatorio': campo.es_obligatorio,
            'es_repetible': campo.es_repetible,
            'es_buscable': campo.es_buscable,
            'es_indexable': campo.es_indexable,
            'orden': campo.orden,
            'valores_posibles': campo.valores_posibles,
            'validador': campo.validador or '',
            'valor_por_defecto': campo.valor_por_defecto or '',
            'ayuda': campo.ayuda or '',
            'categoria': campo.categoria or '',
            'fecha_creacion': campo.fecha_creacion.isoformat() if campo.fecha_creacion else None,
        }
        
        return JsonResponse({
            'success': True,
            'data': campo_dict
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener campo de tipo de proyecto: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "PUT"])
def campo_tipo_proyecto_update(request, campo_id):
    """Actualiza un campo de tipo de proyecto"""
    try:
        campo = get_object_or_404(CampoTipoProyecto, id=campo_id)
        
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
        tipo_proyecto_id = data.get('tipo_proyecto_id')
        if not tipo_proyecto_id:
            return JsonResponse({
                'success': False,
                'error': 'El tipo de proyecto es obligatorio'
            }, status=400)
        
        tipo_proyecto = get_object_or_404(TipoProyecto, id=tipo_proyecto_id)
        
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
        
        # Validar que el slug no exista en otro campo del mismo tipo
        slug = data.get('slug', '').strip()
        if not slug:
            slug = slugify(nombre)
        
        if CampoTipoProyecto.objects.filter(tipo_proyecto=tipo_proyecto, slug=slug).exclude(id=campo_id).exists():
            return JsonResponse({
                'success': False,
                'error': 'Ya existe otro campo con este nombre/slug para este tipo de proyecto'
            }, status=400)
        
        # Procesar valores_posibles
        valores_posibles = data.get('valores_posibles')
        if valores_posibles and isinstance(valores_posibles, str):
            try:
                valores_posibles = json.loads(valores_posibles)
            except:
                valores_posibles = [v.strip() for v in valores_posibles.split(',') if v.strip()]
        
        # Actualizar los campos
        campo.tipo_proyecto = tipo_proyecto
        campo.nombre = nombre
        campo.slug = slug
        campo.etiqueta = etiqueta
        campo.descripcion = data.get('descripcion', '').strip() or None
        campo.tipo_dato = data.get('tipo_dato', 'texto')
        campo.es_obligatorio = data.get('es_obligatorio', False)
        campo.es_repetible = data.get('es_repetible', False)
        campo.es_buscable = data.get('es_buscable', True)
        campo.es_indexable = data.get('es_indexable', True)
        campo.orden = data.get('orden', 0)
        campo.valores_posibles = valores_posibles
        campo.validador = data.get('validador', '').strip() or None
        campo.valor_por_defecto = data.get('valor_por_defecto', '').strip() or None
        campo.ayuda = data.get('ayuda', '').strip() or None
        campo.categoria = data.get('categoria', '').strip() or None
        
        # Validar antes de guardar
        campo.full_clean()
        campo.save()
        
        # Retornar los datos actualizados
        campo_dict = {
            'id': campo.id,
            'tipo_proyecto_id': campo.tipo_proyecto.id,
            'tipo_proyecto_nombre': campo.tipo_proyecto.nombre,
            'nombre': campo.nombre,
            'slug': campo.slug,
            'etiqueta': campo.etiqueta,
            'descripcion': campo.descripcion or '',
            'tipo_dato': campo.tipo_dato,
            'tipo_dato_display': campo.get_tipo_dato_display(),
            'es_obligatorio': campo.es_obligatorio,
            'es_repetible': campo.es_repetible,
            'es_buscable': campo.es_buscable,
            'es_indexable': campo.es_indexable,
            'orden': campo.orden,
            'valores_posibles': campo.valores_posibles,
            'validador': campo.validador or '',
            'valor_por_defecto': campo.valor_por_defecto or '',
            'ayuda': campo.ayuda or '',
            'categoria': campo.categoria or '',
            'fecha_creacion': campo.fecha_creacion.isoformat() if campo.fecha_creacion else None,
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Campo de tipo de proyecto actualizado exitosamente',
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
            'error': f'Error al actualizar campo de tipo de proyecto: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "DELETE"])
def campo_tipo_proyecto_delete(request, campo_id):
    """Elimina un campo de tipo de proyecto"""
    try:
        campo = get_object_or_404(CampoTipoProyecto, id=campo_id)
        
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
                'error': 'No se puede eliminar este campo porque tiene valores asociados en proyectos'
            }, status=400)
        
        # Eliminar el campo
        campo_etiqueta = campo.etiqueta
        campo.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Campo "{campo_etiqueta}" eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al eliminar campo de tipo de proyecto: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def tipos_proyecto_for_select(request):
    """Obtiene la lista de tipos de proyecto para usar en select"""
    tipos = TipoProyecto.objects.filter(es_activo=True).order_by('orden', 'nombre')
    tipos_data = [{'id': tipo.id, 'nombre': tipo.nombre} for tipo in tipos]
    
    return JsonResponse({
        'success': True,
        'data': tipos_data
    })


# ============================================================================
# VISTAS PARA PROYECTOS
# ============================================================================

@login_required
@require_http_methods(["GET"])
def proyectos_list(request):
    """Lista todos los proyectos en formato JSON"""
    from publicaciones.models import Publicacion
    proyectos = Proyecto.objects.select_related('tipo_proyecto', 'creador').prefetch_related('categorias', 'etiquetas', 'autores', 'publicaciones').all()
    proyectos_data = []
    
    for proyecto in proyectos:
        # Obtener autores del proyecto
        autores = []
        for autor in proyecto.autores.select_related('usuario').all().order_by('orden_autor'):
            autores.append({
                'id': autor.id,
                'usuario_id': autor.usuario.id,
                'usuario_nombre': autor.usuario.get_full_name() or autor.usuario.username,
                'nombre_completo': autor.get_nombre_completo(),
                'email': autor.get_email(),
                'afiliacion': autor.get_afiliacion(),
                'orcid_id': autor.get_orcid_id(),
                'orden_autor': autor.orden_autor,
                'es_correspondiente': autor.es_correspondiente,
                'es_autor_principal': autor.es_autor_principal,
            })
        
        # Obtener la primera publicación pública relacionada
        publicacion_publica = proyecto.publicaciones.filter(
            estado='publicada',
            visibilidad='publico'
        ).first()
        
        publicacion_slug = publicacion_publica.slug if publicacion_publica else None
        
        proyecto_dict = {
            'id': proyecto.id,
            'titulo': proyecto.titulo,
            'slug': proyecto.slug,
            'publicacion_slug': publicacion_slug,
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
        }
        proyectos_data.append(proyecto_dict)
    
    return JsonResponse({
        'success': True,
        'data': proyectos_data,
        'total': len(proyectos_data)
    })


@login_required
@require_http_methods(["GET"])
def proyectos_por_tipo(request, tipo_proyecto_id):
    """Lista los proyectos de un tipo específico"""
    tipo_proyecto = get_object_or_404(TipoProyecto, id=tipo_proyecto_id)
    proyectos = Proyecto.objects.filter(tipo_proyecto=tipo_proyecto).select_related('creador').prefetch_related('categorias', 'etiquetas')
    proyectos_data = []
    
    for proyecto in proyectos:
        proyecto_dict = {
            'id': proyecto.id,
            'titulo': proyecto.titulo,
            'slug': proyecto.slug,
            'creador_id': proyecto.creador.id,
            'creador_nombre': proyecto.creador.get_full_name() or proyecto.creador.username,
            'estado': proyecto.estado,
            'estado_display': proyecto.get_estado_display(),
            'fecha_creacion': proyecto.fecha_creacion.isoformat() if proyecto.fecha_creacion else None,
            'fecha_publicacion': proyecto.fecha_publicacion.isoformat() if proyecto.fecha_publicacion else None,
        }
        proyectos_data.append(proyecto_dict)
    
    return JsonResponse({
        'success': True,
        'data': proyectos_data,
        'tipo_proyecto': {
            'id': tipo_proyecto.id,
            'nombre': tipo_proyecto.nombre
        },
        'total': len(proyectos_data)
    })


@login_required
@require_http_methods(["GET"])
def campos_por_tipo_proyecto(request, tipo_proyecto_id):
    """Obtiene los campos dinámicos de un tipo de proyecto"""
    try:
        tipo_proyecto = get_object_or_404(TipoProyecto, id=tipo_proyecto_id)
        campos = CampoTipoProyecto.objects.filter(tipo_proyecto=tipo_proyecto).order_by('orden', 'categoria', 'nombre')
        
        campos_data = []
        for campo in campos:
            campo_dict = {
                'id': campo.id,
                'nombre': campo.nombre,
                'slug': campo.slug,
                'etiqueta': campo.etiqueta,
                'descripcion': campo.descripcion or '',
                'tipo_dato': campo.tipo_dato,
                'tipo_dato_display': campo.get_tipo_dato_display(),
                'es_obligatorio': campo.es_obligatorio,
                'es_repetible': campo.es_repetible,
                'valores_posibles': campo.valores_posibles,
                'valor_por_defecto': campo.valor_por_defecto or '',
                'ayuda': campo.ayuda or '',
                'categoria': campo.categoria or '',
                'orden': campo.orden,
            }
            campos_data.append(campo_dict)
        
        return JsonResponse({
            'success': True,
            'data': campos_data,
            'tipo_proyecto': {
                'id': tipo_proyecto.id,
                'nombre': tipo_proyecto.nombre
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener campos: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def proyecto_detail(request, proyecto_id):
    """Obtiene los detalles de un proyecto"""
    try:
        proyecto = get_object_or_404(
            Proyecto.objects.select_related('tipo_proyecto', 'creador').prefetch_related('autores'), 
            id=proyecto_id
        )
        
        # Obtener valores de campos dinámicos
        valores_campos = {}
        for valor_campo in proyecto.valores_campos.select_related('campo_tipo_proyecto').all():
            campo_slug = valor_campo.campo_tipo_proyecto.slug
            if campo_slug not in valores_campos:
                valores_campos[campo_slug] = []
            
            valores_campos[campo_slug].append({
                'valor': valor_campo.get_valor(),
                'orden': valor_campo.orden
            })
        
        # Obtener autores del proyecto
        autores = []
        for autor in proyecto.autores.all().select_related('usuario').order_by('orden_autor'):
            autores.append({
                'id': autor.id,
                'usuario_id': autor.usuario.id,
                'usuario_nombre': autor.usuario.get_full_name() or autor.usuario.username,
                'usuario_username': autor.usuario.username,
                'nombre_completo': autor.get_nombre_completo(),
                'nombre': autor.get_nombre(),
                'apellidos': autor.get_apellidos(),
                'email': autor.get_email(),
                'afiliacion': autor.get_afiliacion(),
                'orcid_id': autor.get_orcid_id(),
                'orden_autor': autor.orden_autor,
                'es_correspondiente': autor.es_correspondiente,
                'es_autor_principal': autor.es_autor_principal,
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
            'valores_campos': valores_campos,
        }
        
        return JsonResponse({
            'success': True,
            'data': proyecto_dict
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener proyecto: {str(e)}'
        }, status=500)


from repositorio.models import Documento, VersionDocumento, Archivo

@login_required
@require_http_methods(["POST"])
@transaction.atomic
def proyecto_create(request):
    """Crea un nuevo proyecto con campos dinámicos y subida de archivo."""
    try:
        # Los datos ahora vienen de request.POST y request.FILES
        data = request.POST
        
        # Validar campos requeridos
        titulo = data.get('titulo', '').strip()
        if not titulo:
            return JsonResponse({'success': False, 'error': 'El título es obligatorio'}, status=400)
        
        tipo_proyecto_id = data.get('tipo_proyecto_id')
        if not tipo_proyecto_id:
            return JsonResponse({'success': False, 'error': 'El tipo de proyecto es obligatorio'}, status=400)
        
        tipo_proyecto = get_object_or_404(TipoProyecto, id=tipo_proyecto_id)
        
        # Generar slug
        nuevo_slug = slugify(titulo)
        if not nuevo_slug:
            return JsonResponse({'success': False, 'error': 'El título no puede generar un slug válido'}, status=400)
        
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
            resumen=data.get('resumen', '').strip() or None,
            descripcion=data.get('descripcion', '').strip() or None,
            estado=data.get('estado', 'borrador'),
            visibilidad=data.get('visibilidad', 'publico'),
            version=1
        )
        proyecto.full_clean()
        proyecto.save()
        
        # Manejar subida de archivo
        if 'archivo' in request.FILES:
            uploaded_file = request.FILES['archivo']
            
            # 1. Crear Documento
            documento = Documento.objects.create(
                proyecto=proyecto,
                creador=request.user,
                titulo=proyecto.titulo, # Usar título del proyecto
                resumen=proyecto.resumen, # Usar resumen del proyecto
                visibilidad=proyecto.visibilidad
            )
            
            # 2. Crear VersionDocumento
            version = VersionDocumento.objects.create(
                documento=documento,
                numero_version=1,
                creado_por=request.user,
                es_version_actual=True
            )
            
            # 3. Crear Archivo y asociarlo a la versión
            Archivo.objects.create(
                version=version,
                archivo=uploaded_file,
                nombre_original=uploaded_file.name,
                tamaño_bytes=uploaded_file.size,
                tipo_mime=uploaded_file.content_type,
                es_archivo_principal=True
            )

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
        for autor_data in autores_data:
            usuario_id = autor_data.get('usuario_id')
            if usuario_id:
                usuario = get_object_or_404(User, id=usuario_id)
                if not ProyectoAutor.objects.filter(proyecto=proyecto, usuario=usuario).exists():
                    ProyectoAutor.objects.create(
                        proyecto=proyecto,
                        usuario=usuario,
                        orden_autor=autor_data.get('orden_autor', 1)
                    )

        # Retornar respuesta
        return JsonResponse({
            'success': True,
            'message': 'Proyecto creado exitosamente',
            'data': {'id': proyecto.id, 'titulo': proyecto.titulo}
        })
        
    except (ValidationError, json.JSONDecodeError) as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error inesperado: {str(e)}'}, status=500)


@login_required
@require_http_methods(["POST", "PUT"])
def proyecto_update(request, proyecto_id):
    """Actualiza un proyecto existente"""
    try:
        proyecto = get_object_or_404(Proyecto, id=proyecto_id)
        
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
        titulo = data.get('titulo', '').strip()
        if not titulo:
            return JsonResponse({
                'success': False,
                'error': 'El título es obligatorio'
            }, status=400)
        
        # Actualizar campos básicos
        proyecto.titulo = titulo
        
        # Actualizar slug si cambió el título
        nuevo_slug = slugify(titulo)
        if nuevo_slug != proyecto.slug:
            slug_base = nuevo_slug
            contador = 1
            while Proyecto.objects.filter(slug=nuevo_slug).exclude(id=proyecto_id).exists():
                nuevo_slug = f"{slug_base}-{contador}"
                contador += 1
            proyecto.slug = nuevo_slug
        
        proyecto.resumen = data.get('resumen', '').strip() or None
        proyecto.descripcion = data.get('descripcion', '').strip() or None
        proyecto.estado = data.get('estado', proyecto.estado)
        proyecto.visibilidad = data.get('visibilidad', proyecto.visibilidad)
        
        proyecto.full_clean()
        proyecto.save()
        
        # Actualizar valores de campos dinámicos
        campos_dinamicos = data.get('campos_dinamicos', {})
        if campos_dinamicos:
            # Eliminar valores existentes
            proyecto.valores_campos.all().delete()
            
            # Crear nuevos valores
            for campo_slug, valores in campos_dinamicos.items():
                try:
                    campo_tipo = CampoTipoProyecto.objects.get(tipo_proyecto=proyecto.tipo_proyecto, slug=campo_slug)
                    
                    if campo_tipo.es_repetible and isinstance(valores, list):
                        for orden, valor in enumerate(valores):
                            valor_campo = ValorCampoProyecto(
                                proyecto=proyecto,
                                campo_tipo_proyecto=campo_tipo,
                                orden=orden
                            )
                            valor_campo.set_valor(valor)
                            valor_campo.save()
                    else:
                        valor = valores[0] if isinstance(valores, list) and valores else valores
                        if valor is not None and valor != '':
                            valor_campo = ValorCampoProyecto(
                                proyecto=proyecto,
                                campo_tipo_proyecto=campo_tipo,
                                orden=0
                            )
                            valor_campo.set_valor(valor)
                            valor_campo.save()
                except CampoTipoProyecto.DoesNotExist:
                    continue
        
        # Actualizar autores del proyecto
        autores_data = data.get('autores', [])
        if autores_data is not None:
            # Obtener IDs de autores que se van a mantener (solo los que tienen ID y no son None)
            autores_ids_mantener = [int(a.get('id')) for a in autores_data if a.get('id') and a.get('id') is not None]
            
            # Obtener IDs de usuarios que se van a agregar (nuevos autores)
            usuarios_ids_nuevos = [int(a.get('usuario_id')) for a in autores_data if a.get('usuario_id')]
            
            # Eliminar autores existentes que no estén en la nueva lista
            if autores_ids_mantener:
                ProyectoAutor.objects.filter(proyecto=proyecto).exclude(id__in=autores_ids_mantener).delete()
            else:
                # Si no hay IDs para mantener, eliminar todos los autores existentes
                ProyectoAutor.objects.filter(proyecto=proyecto).delete()
            
            # Actualizar o crear autores
            for autor_data in autores_data:
                usuario_id = autor_data.get('usuario_id')
                if not usuario_id:
                    continue  # Saltar si no hay usuario_id
                
                usuario = get_object_or_404(User, id=usuario_id)
                autor_id = autor_data.get('id')
                
                if autor_id and autor_id is not None:
                    # Actualizar autor existente
                    try:
                        autor = ProyectoAutor.objects.get(id=autor_id, proyecto=proyecto)
                        # Verificar que el usuario no haya cambiado (no se permite cambiar usuario)
                        if autor.usuario.id != usuario.id:
                            # Si cambió el usuario, eliminar el autor antiguo y crear uno nuevo
                            autor.delete()
                            ProyectoAutor.objects.create(
                                proyecto=proyecto,
                                usuario=usuario,
                                afiliacion=autor_data.get('afiliacion') or None,
                                orcid_id=autor_data.get('orcid_id') or None,
                                orden_autor=autor_data.get('orden_autor', 1),
                                es_correspondiente=autor_data.get('es_correspondiente', False),
                                es_autor_principal=autor_data.get('es_autor_principal', False),
                            )
                        else:
                            # Actualizar campos opcionales
                            autor.afiliacion = autor_data.get('afiliacion') or None
                            autor.orcid_id = autor_data.get('orcid_id') or None
                            autor.orden_autor = autor_data.get('orden_autor', autor.orden_autor)
                            autor.es_correspondiente = autor_data.get('es_correspondiente', False)
                            autor.es_autor_principal = autor_data.get('es_autor_principal', False)
                            autor.save()
                    except (ProyectoAutor.DoesNotExist, ValueError):
                        # Si el autor no existe o el ID es inválido, crear uno nuevo
                        # Verificar que el usuario no sea ya autor de este proyecto
                        if not ProyectoAutor.objects.filter(proyecto=proyecto, usuario=usuario).exists():
                            ProyectoAutor.objects.create(
                                proyecto=proyecto,
                                usuario=usuario,
                                afiliacion=autor_data.get('afiliacion') or None,
                                orcid_id=autor_data.get('orcid_id') or None,
                                orden_autor=autor_data.get('orden_autor', 1),
                                es_correspondiente=autor_data.get('es_correspondiente', False),
                                es_autor_principal=autor_data.get('es_autor_principal', False),
                            )
                else:
                    # Crear nuevo autor (sin ID o ID es None)
                    # Verificar que el usuario no sea ya autor de este proyecto
                    if not ProyectoAutor.objects.filter(proyecto=proyecto, usuario=usuario).exists():
                        ProyectoAutor.objects.create(
                            proyecto=proyecto,
                            usuario=usuario,
                            afiliacion=autor_data.get('afiliacion') or None,
                            orcid_id=autor_data.get('orcid_id') or None,
                            orden_autor=autor_data.get('orden_autor', 1),
                            es_correspondiente=autor_data.get('es_correspondiente', False),
                            es_autor_principal=autor_data.get('es_autor_principal', False),
                        )
        
        # Retornar los datos actualizados
        proyecto.refresh_from_db()
        autores = []
        for autor in proyecto.autores.select_related('usuario').all().order_by('orden_autor'):
            autores.append({
                'id': autor.id,
                'usuario_id': autor.usuario.id,
                'usuario_nombre': autor.usuario.get_full_name() or autor.usuario.username,
                'nombre_completo': autor.get_nombre_completo(),
            })
        
        proyecto_dict = {
            'id': proyecto.id,
            'titulo': proyecto.titulo,
            'slug': proyecto.slug,
            'tipo_proyecto_id': proyecto.tipo_proyecto.id,
            'tipo_proyecto_nombre': proyecto.tipo_proyecto.nombre,
            'estado': proyecto.estado,
            'estado_display': proyecto.get_estado_display(),
            'autores_count': proyecto.autores.count(),
            'autores': autores,
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Proyecto actualizado exitosamente',
            'data': proyecto_dict
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
@require_http_methods(["GET"])
def usuarios_for_select(request):
    """Obtiene los usuarios activos para usar en selects de autores"""
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
                'first_name': usuario.first_name or '',
                'last_name': usuario.last_name or '',
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
@require_http_methods(["POST", "DELETE"])
def proyecto_delete(request, proyecto_id):
    """Elimina un proyecto"""
    try:
        proyecto = get_object_or_404(Proyecto, id=proyecto_id)
        
        # Manejar tanto POST con _method como DELETE directo
        if request.method == 'POST':
            data = json.loads(request.body) if request.body else {}
            if data.get('_method') != 'DELETE':
                return JsonResponse({
                    'success': False,
                    'error': 'Método no permitido'
                }, status=405)
        
        # Eliminar el proyecto (esto también eliminará los valores de campos por CASCADE)
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
