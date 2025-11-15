from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse, FileResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.forms.models import model_to_dict
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.db import transaction
import json
import uuid
import hashlib
import os
from datetime import datetime
from .models import TipoRecurso, EstadoDocumento, Comunidad, Coleccion, Licencia, Documento, Autor, Colaborador, VersionDocumento, Archivo
from catalogacion.models import Categoria, Etiqueta


@login_required
@ensure_csrf_cookie
@require_http_methods(["GET"])
def index(request):
    """Vista principal del repositorio - Redirige a configuración"""
    return redirect('repositorio:configuracion')


@login_required
@ensure_csrf_cookie
@require_http_methods(["GET"])
def configuracion(request):
    """Vista de configuración del repositorio (Tipos de Recurso, Estados, Licencias)"""
    # Verificar permisos
    if not (request.user.has_perm('repositorio.view_tiporecurso') or 
            request.user.has_perm('repositorio.view_estadodocumento') or
            request.user.has_perm('repositorio.view_licencia') or
            request.user.is_superuser):
        messages.warning(request, 'No tienes permisos para acceder a configuración del repositorio.')
        return redirect('usuarios:panel')
    
    return render(request, 'repositorio/configuracion.html')


@login_required
@ensure_csrf_cookie
@require_http_methods(["GET"])
def organizacion(request):
    """Vista de organización del repositorio (Comunidades, Colecciones, Documentos)"""
    # Verificar permisos
    if not (request.user.has_perm('repositorio.view_comunidad') or
            request.user.has_perm('repositorio.view_coleccion') or
            request.user.has_perm('repositorio.view_documento') or
            request.user.is_superuser):
        messages.warning(request, 'No tienes permisos para acceder a organización del repositorio.')
        return redirect('usuarios:panel')
    
    return render(request, 'repositorio/organizacion.html')


@login_required
@ensure_csrf_cookie
@require_http_methods(["GET"])
def personal(request):
    """Vista de personal del repositorio (Autores, Colaboradores)"""
    # Verificar permisos
    if not (request.user.has_perm('repositorio.view_autor') or
            request.user.has_perm('repositorio.view_colaborador') or
            request.user.is_superuser):
        messages.warning(request, 'No tienes permisos para acceder a personal del repositorio.')
        return redirect('usuarios:panel')
    
    return render(request, 'repositorio/personal.html')


# ========================================================================
# TIPOS DE RECURSO
# ========================================================================

@login_required
@require_http_methods(["GET"])
def tipos_recurso_list(request):
    """Lista todos los tipos de recurso"""
    try:
        tipos = TipoRecurso.objects.all().order_by('nombre')
        tipos_data = []
        
        for tipo in tipos:
            tipo_dict = {
                'id': tipo.id,
                'nombre': tipo.nombre,
                'descripcion': tipo.descripcion or '',
                'icono': tipo.icono or '',
                'categoria': tipo.categoria or '',
            }
            tipos_data.append(tipo_dict)
        
        return JsonResponse({
            'success': True,
            'data': tipos_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener tipos de recurso: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def tipo_recurso_create(request):
    """Crea un nuevo tipo de recurso"""
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
        if TipoRecurso.objects.filter(nombre=nombre).exists():
            return JsonResponse({
                'success': False,
                'error': 'Ya existe un tipo de recurso con este nombre'
            }, status=400)
        
        # Crear el tipo de recurso
        tipo = TipoRecurso(
            nombre=nombre,
            descripcion=data.get('descripcion', '').strip() or None,
            icono=data.get('icono', '').strip() or None,
            categoria=data.get('categoria', '').strip() or None,
        )
        
        tipo.full_clean()
        tipo.save()
        
        # Retornar los datos del tipo creado
        tipo_dict = {
            'id': tipo.id,
            'nombre': tipo.nombre,
            'descripcion': tipo.descripcion or '',
            'icono': tipo.icono or '',
            'categoria': tipo.categoria or '',
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Tipo de recurso creado exitosamente',
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
            'error': f'Error al crear tipo de recurso: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def tipo_recurso_detail(request, tipo_recurso_id):
    """Obtiene los detalles de un tipo de recurso"""
    try:
        tipo = get_object_or_404(TipoRecurso, id=tipo_recurso_id)
        
        tipo_dict = {
            'id': tipo.id,
            'nombre': tipo.nombre,
            'descripcion': tipo.descripcion or '',
            'icono': tipo.icono or '',
            'categoria': tipo.categoria or '',
        }
        
        return JsonResponse({
            'success': True,
            'data': tipo_dict
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener tipo de recurso: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "PUT"])
def tipo_recurso_update(request, tipo_recurso_id):
    """Actualiza un tipo de recurso"""
    try:
        tipo = get_object_or_404(TipoRecurso, id=tipo_recurso_id)
        
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
        if TipoRecurso.objects.filter(nombre=nombre).exclude(id=tipo_recurso_id).exists():
            return JsonResponse({
                'success': False,
                'error': 'Ya existe otro tipo de recurso con este nombre'
            }, status=400)
        
        # Actualizar los campos
        tipo.nombre = nombre
        tipo.descripcion = data.get('descripcion', '').strip() or None
        tipo.icono = data.get('icono', '').strip() or None
        tipo.categoria = data.get('categoria', '').strip() or None
        
        tipo.full_clean()
        tipo.save()
        
        # Retornar los datos actualizados
        tipo_dict = {
            'id': tipo.id,
            'nombre': tipo.nombre,
            'descripcion': tipo.descripcion or '',
            'icono': tipo.icono or '',
            'categoria': tipo.categoria or '',
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Tipo de recurso actualizado exitosamente',
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
            'error': f'Error al actualizar tipo de recurso: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "DELETE"])
def tipo_recurso_delete(request, tipo_recurso_id):
    """Elimina un tipo de recurso"""
    try:
        tipo = get_object_or_404(TipoRecurso, id=tipo_recurso_id)
        
        # Manejar tanto POST con _method como DELETE directo
        if request.method == 'POST':
            data = json.loads(request.body) if request.body else {}
            if data.get('_method') != 'DELETE':
                return JsonResponse({
                    'success': False,
                    'error': 'Método no permitido'
                }, status=405)
        
        # Verificar si hay documentos usando este tipo de recurso
        from .models import Documento
        if Documento.objects.filter(tipo_recurso=tipo).exists():
            return JsonResponse({
                'success': False,
                'error': 'No se puede eliminar este tipo de recurso porque hay documentos que lo están usando'
            }, status=400)
        
        # Eliminar el tipo de recurso
        tipo_nombre = tipo.nombre
        tipo.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Tipo de recurso "{tipo_nombre}" eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al eliminar tipo de recurso: {str(e)}'
        }, status=500)


# ========================================================================
# ESTADOS DE DOCUMENTO
# ========================================================================

@login_required
@require_http_methods(["GET"])
def estados_documento_list(request):
    """Lista todos los estados de documento"""
    try:
        estados = EstadoDocumento.objects.all().order_by('orden', 'nombre')
        estados_data = []
        
        for estado in estados:
            estado_dict = {
                'id': estado.id,
                'nombre': estado.nombre,
                'descripcion': estado.descripcion or '',
                'orden': estado.orden,
            }
            estados_data.append(estado_dict)
        
        return JsonResponse({
            'success': True,
            'data': estados_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener estados de documento: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def estado_documento_create(request):
    """Crea un nuevo estado de documento"""
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
        if EstadoDocumento.objects.filter(nombre=nombre).exists():
            return JsonResponse({
                'success': False,
                'error': 'Ya existe un estado de documento con este nombre'
            }, status=400)
        
        # Crear el estado de documento
        estado = EstadoDocumento(
            nombre=nombre,
            descripcion=data.get('descripcion', '').strip() or None,
            orden=data.get('orden', 0),
        )
        
        estado.full_clean()
        estado.save()
        
        # Retornar los datos del estado creado
        estado_dict = {
            'id': estado.id,
            'nombre': estado.nombre,
            'descripcion': estado.descripcion or '',
            'orden': estado.orden,
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Estado de documento creado exitosamente',
            'data': estado_dict
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
            'error': f'Error al crear estado de documento: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def estado_documento_detail(request, estado_documento_id):
    """Obtiene los detalles de un estado de documento"""
    try:
        estado = get_object_or_404(EstadoDocumento, id=estado_documento_id)
        
        estado_dict = {
            'id': estado.id,
            'nombre': estado.nombre,
            'descripcion': estado.descripcion or '',
            'orden': estado.orden,
        }
        
        return JsonResponse({
            'success': True,
            'data': estado_dict
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener estado de documento: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "PUT"])
def estado_documento_update(request, estado_documento_id):
    """Actualiza un estado de documento"""
    try:
        estado = get_object_or_404(EstadoDocumento, id=estado_documento_id)
        
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
        
        # Validar que el nombre no exista en otro estado
        if EstadoDocumento.objects.filter(nombre=nombre).exclude(id=estado_documento_id).exists():
            return JsonResponse({
                'success': False,
                'error': 'Ya existe otro estado de documento con este nombre'
            }, status=400)
        
        # Actualizar los campos
        estado.nombre = nombre
        estado.descripcion = data.get('descripcion', '').strip() or None
        estado.orden = data.get('orden', 0)
        
        estado.full_clean()
        estado.save()
        
        # Retornar los datos actualizados
        estado_dict = {
            'id': estado.id,
            'nombre': estado.nombre,
            'descripcion': estado.descripcion or '',
            'orden': estado.orden,
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Estado de documento actualizado exitosamente',
            'data': estado_dict
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
            'error': f'Error al actualizar estado de documento: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "DELETE"])
def estado_documento_delete(request, estado_documento_id):
    """Elimina un estado de documento"""
    try:
        estado = get_object_or_404(EstadoDocumento, id=estado_documento_id)
        
        # Manejar tanto POST con _method como DELETE directo
        if request.method == 'POST':
            data = json.loads(request.body) if request.body else {}
            if data.get('_method') != 'DELETE':
                return JsonResponse({
                    'success': False,
                    'error': 'Método no permitido'
                }, status=405)
        
        # Verificar si hay documentos usando este estado
        from .models import Documento
        if Documento.objects.filter(estado=estado).exists():
            return JsonResponse({
                'success': False,
                'error': 'No se puede eliminar este estado porque hay documentos que lo están usando'
            }, status=400)
        
        # Eliminar el estado de documento
        estado_nombre = estado.nombre
        estado.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Estado de documento "{estado_nombre}" eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al eliminar estado de documento: {str(e)}'
        }, status=500)


# ========================================================================
# COMUNIDADES
# ========================================================================

@login_required
@require_http_methods(["GET"])
def comunidades_list(request):
    """Lista todas las comunidades"""
    try:
        comunidades = Comunidad.objects.all().order_by('nombre')
        comunidades_data = []
        
        for comunidad in comunidades:
            comunidad_dict = {
                'id': comunidad.id,
                'nombre': comunidad.nombre,
                'slug': comunidad.slug,
                'descripcion': comunidad.descripcion or '',
                'logo': comunidad.logo or '',
                'banner': comunidad.banner or '',
                'comunidad_padre_id': comunidad.comunidad_padre.id if comunidad.comunidad_padre else None,
                'comunidad_padre_nombre': comunidad.comunidad_padre.nombre if comunidad.comunidad_padre else '',
                'administrador_id': comunidad.administrador.id,
                'administrador_nombre': comunidad.administrador.get_full_name() or comunidad.administrador.username,
                'es_publica': comunidad.es_publica,
                'estado': comunidad.estado,
                'fecha_creacion': comunidad.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S'),
            }
            comunidades_data.append(comunidad_dict)
        
        return JsonResponse({
            'success': True,
            'data': comunidades_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener comunidades: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def comunidades_for_select(request):
    """Obtiene las comunidades para usar en selects"""
    try:
        comunidades = Comunidad.objects.all().order_by('nombre')
        comunidades_data = [{'id': c.id, 'nombre': c.nombre} for c in comunidades]
        
        return JsonResponse({
            'success': True,
            'data': comunidades_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener comunidades: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def usuarios_for_select(request):
    """Obtiene los usuarios para usar en selects"""
    try:
        usuarios = User.objects.filter(is_active=True).order_by('username')
        usuarios_data = [{'id': u.id, 'nombre': u.get_full_name() or u.username, 'username': u.username} for u in usuarios]
        
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
@require_http_methods(["POST"])
def comunidad_create(request):
    """Crea una nueva comunidad"""
    try:
        data = json.loads(request.body)
        
        # Validar campos requeridos
        nombre = data.get('nombre', '').strip()
        if not nombre:
            return JsonResponse({
                'success': False,
                'error': 'El nombre es obligatorio'
            }, status=400)
        
        # Validar administrador
        administrador_id = data.get('administrador_id')
        if not administrador_id:
            return JsonResponse({
                'success': False,
                'error': 'El administrador es obligatorio'
            }, status=400)
        
        try:
            administrador = User.objects.get(id=administrador_id)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'El usuario administrador no existe'
            }, status=400)
        
        # Generar slug
        slug = slugify(nombre)
        if not slug:
            return JsonResponse({
                'success': False,
                'error': 'No se pudo generar un slug válido desde el nombre'
            }, status=400)
        
        # Validar que el slug sea único
        if Comunidad.objects.filter(slug=slug).exists():
            return JsonResponse({
                'success': False,
                'error': 'Ya existe una comunidad con este nombre (slug duplicado)'
            }, status=400)
        
        # Validar comunidad_padre si existe
        comunidad_padre_id = data.get('comunidad_padre_id')
        comunidad_padre = None
        if comunidad_padre_id:
            try:
                comunidad_padre = Comunidad.objects.get(id=comunidad_padre_id)
            except Comunidad.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'La comunidad padre no existe'
                }, status=400)
        
        # Crear la comunidad
        comunidad = Comunidad(
            nombre=nombre,
            slug=slug,
            descripcion=data.get('descripcion', '').strip() or None,
            logo=data.get('logo', '').strip() or None,
            banner=data.get('banner', '').strip() or None,
            comunidad_padre=comunidad_padre,
            administrador=administrador,
            es_publica=data.get('es_publica', True),
            estado=data.get('estado', 'activa'),
        )
        
        comunidad.full_clean()
        comunidad.save()
        
        # Retornar los datos de la comunidad creada
        comunidad_dict = {
            'id': comunidad.id,
            'nombre': comunidad.nombre,
            'slug': comunidad.slug,
            'descripcion': comunidad.descripcion or '',
            'logo': comunidad.logo or '',
            'banner': comunidad.banner or '',
            'comunidad_padre_id': comunidad.comunidad_padre.id if comunidad.comunidad_padre else None,
            'comunidad_padre_nombre': comunidad.comunidad_padre.nombre if comunidad.comunidad_padre else '',
            'administrador_id': comunidad.administrador.id,
            'administrador_nombre': comunidad.administrador.get_full_name() or comunidad.administrador.username,
            'es_publica': comunidad.es_publica,
            'estado': comunidad.estado,
            'fecha_creacion': comunidad.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S'),
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Comunidad creada exitosamente',
            'data': comunidad_dict
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
            'error': f'Error al crear comunidad: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def comunidad_detail(request, comunidad_id):
    """Obtiene los detalles de una comunidad"""
    try:
        comunidad = get_object_or_404(Comunidad, id=comunidad_id)
        
        comunidad_dict = {
            'id': comunidad.id,
            'nombre': comunidad.nombre,
            'slug': comunidad.slug,
            'descripcion': comunidad.descripcion or '',
            'logo': comunidad.logo or '',
            'banner': comunidad.banner or '',
            'comunidad_padre_id': comunidad.comunidad_padre.id if comunidad.comunidad_padre else None,
            'comunidad_padre_nombre': comunidad.comunidad_padre.nombre if comunidad.comunidad_padre else '',
            'administrador_id': comunidad.administrador.id,
            'administrador_nombre': comunidad.administrador.get_full_name() or comunidad.administrador.username,
            'es_publica': comunidad.es_publica,
            'estado': comunidad.estado,
            'fecha_creacion': comunidad.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S'),
        }
        
        return JsonResponse({
            'success': True,
            'data': comunidad_dict
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener comunidad: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "PUT"])
def comunidad_update(request, comunidad_id):
    """Actualiza una comunidad"""
    try:
        comunidad = get_object_or_404(Comunidad, id=comunidad_id)
        
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
        
        # Validar administrador
        administrador_id = data.get('administrador_id')
        if not administrador_id:
            return JsonResponse({
                'success': False,
                'error': 'El administrador es obligatorio'
            }, status=400)
        
        try:
            administrador = User.objects.get(id=administrador_id)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'El usuario administrador no existe'
            }, status=400)
        
        # Generar slug si el nombre cambió
        nuevo_slug = slugify(nombre)
        if not nuevo_slug:
            return JsonResponse({
                'success': False,
                'error': 'No se pudo generar un slug válido desde el nombre'
            }, status=400)
        
        # Validar que el slug sea único (excepto para esta comunidad)
        if Comunidad.objects.filter(slug=nuevo_slug).exclude(id=comunidad_id).exists():
            return JsonResponse({
                'success': False,
                'error': 'Ya existe otra comunidad con este nombre (slug duplicado)'
            }, status=400)
        
        # Validar comunidad_padre si existe
        comunidad_padre_id = data.get('comunidad_padre_id')
        comunidad_padre = None
        if comunidad_padre_id:
            try:
                comunidad_padre = Comunidad.objects.get(id=comunidad_padre_id)
                # Evitar referencia circular
                if comunidad_padre.id == comunidad_id:
                    return JsonResponse({
                        'success': False,
                        'error': 'Una comunidad no puede ser su propia padre'
                    }, status=400)
            except Comunidad.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'La comunidad padre no existe'
                }, status=400)
        
        # Actualizar los campos
        comunidad.nombre = nombre
        comunidad.slug = nuevo_slug
        comunidad.descripcion = data.get('descripcion', '').strip() or None
        comunidad.logo = data.get('logo', '').strip() or None
        comunidad.banner = data.get('banner', '').strip() or None
        comunidad.comunidad_padre = comunidad_padre
        comunidad.administrador = administrador
        comunidad.es_publica = data.get('es_publica', True)
        comunidad.estado = data.get('estado', 'activa')
        
        comunidad.full_clean()
        comunidad.save()
        
        # Retornar los datos actualizados
        comunidad_dict = {
            'id': comunidad.id,
            'nombre': comunidad.nombre,
            'slug': comunidad.slug,
            'descripcion': comunidad.descripcion or '',
            'logo': comunidad.logo or '',
            'banner': comunidad.banner or '',
            'comunidad_padre_id': comunidad.comunidad_padre.id if comunidad.comunidad_padre else None,
            'comunidad_padre_nombre': comunidad.comunidad_padre.nombre if comunidad.comunidad_padre else '',
            'administrador_id': comunidad.administrador.id,
            'administrador_nombre': comunidad.administrador.get_full_name() or comunidad.administrador.username,
            'es_publica': comunidad.es_publica,
            'estado': comunidad.estado,
            'fecha_creacion': comunidad.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S'),
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Comunidad actualizada exitosamente',
            'data': comunidad_dict
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
            'error': f'Error al actualizar comunidad: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "DELETE"])
def comunidad_delete(request, comunidad_id):
    """Elimina una comunidad"""
    try:
        comunidad = get_object_or_404(Comunidad, id=comunidad_id)
        
        # Manejar tanto POST con _method como DELETE directo
        if request.method == 'POST':
            data = json.loads(request.body) if request.body else {}
            if data.get('_method') != 'DELETE':
                return JsonResponse({
                    'success': False,
                    'error': 'Método no permitido'
                }, status=405)
        
        # Verificar si hay colecciones o subcomunidades usando esta comunidad
        if comunidad.colecciones.exists():
            return JsonResponse({
                'success': False,
                'error': 'No se puede eliminar esta comunidad porque tiene colecciones asociadas'
            }, status=400)
        
        if comunidad.subcomunidades.exists():
            return JsonResponse({
                'success': False,
                'error': 'No se puede eliminar esta comunidad porque tiene subcomunidades asociadas'
            }, status=400)
        
        # Eliminar la comunidad
        comunidad_nombre = comunidad.nombre
        comunidad.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Comunidad "{comunidad_nombre}" eliminada exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al eliminar comunidad: {str(e)}'
        }, status=500)


# ========================================================================
# COLECCIONES
# ========================================================================

@login_required
@require_http_methods(["GET"])
def colecciones_list(request):
    """Lista todas las colecciones"""
    try:
        colecciones = Coleccion.objects.select_related('comunidad', 'administrador', 'coleccion_padre').all().order_by('comunidad__nombre', 'nombre')
        colecciones_data = []
        
        for coleccion in colecciones:
            coleccion_dict = {
                'id': coleccion.id,
                'nombre': coleccion.nombre,
                'slug': coleccion.slug,
                'descripcion': coleccion.descripcion or '',
                'comunidad_id': coleccion.comunidad.id,
                'comunidad_nombre': coleccion.comunidad.nombre,
                'coleccion_padre_id': coleccion.coleccion_padre.id if coleccion.coleccion_padre else None,
                'coleccion_padre_nombre': coleccion.coleccion_padre.nombre if coleccion.coleccion_padre else '',
                'administrador_id': coleccion.administrador.id,
                'administrador_nombre': coleccion.administrador.get_full_name() or coleccion.administrador.username,
                'politica_ingreso': coleccion.politica_ingreso,
                'es_publica': coleccion.es_publica,
                'fecha_creacion': coleccion.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S'),
            }
            colecciones_data.append(coleccion_dict)
        
        return JsonResponse({
            'success': True,
            'data': colecciones_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener colecciones: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def colecciones_por_comunidad(request, comunidad_id):
    """Obtiene las colecciones de una comunidad específica"""
    try:
        colecciones = Coleccion.objects.filter(comunidad_id=comunidad_id).order_by('nombre')
        colecciones_data = [{'id': c.id, 'nombre': c.nombre} for c in colecciones]
        
        return JsonResponse({
            'success': True,
            'data': colecciones_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener colecciones: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def coleccion_create(request):
    """Crea una nueva colección"""
    try:
        data = json.loads(request.body)
        
        # Validar campos requeridos
        nombre = data.get('nombre', '').strip()
        if not nombre:
            return JsonResponse({
                'success': False,
                'error': 'El nombre es obligatorio'
            }, status=400)
        
        # Validar comunidad
        comunidad_id = data.get('comunidad_id')
        if not comunidad_id:
            return JsonResponse({
                'success': False,
                'error': 'La comunidad es obligatoria'
            }, status=400)
        
        try:
            comunidad = Comunidad.objects.get(id=comunidad_id)
        except Comunidad.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'La comunidad no existe'
            }, status=400)
        
        # Validar administrador
        administrador_id = data.get('administrador_id')
        if not administrador_id:
            return JsonResponse({
                'success': False,
                'error': 'El administrador es obligatorio'
            }, status=400)
        
        try:
            administrador = User.objects.get(id=administrador_id)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'El usuario administrador no existe'
            }, status=400)
        
        # Generar slug
        slug = slugify(nombre)
        if not slug:
            return JsonResponse({
                'success': False,
                'error': 'No se pudo generar un slug válido desde el nombre'
            }, status=400)
        
        # Validar que el slug sea único dentro de la comunidad
        if Coleccion.objects.filter(slug=slug, comunidad=comunidad).exists():
            return JsonResponse({
                'success': False,
                'error': 'Ya existe una colección con este nombre en esta comunidad'
            }, status=400)
        
        # Validar coleccion_padre si existe
        coleccion_padre_id = data.get('coleccion_padre_id')
        coleccion_padre = None
        if coleccion_padre_id:
            try:
                coleccion_padre = Coleccion.objects.get(id=coleccion_padre_id)
                # Verificar que pertenezca a la misma comunidad
                if coleccion_padre.comunidad.id != comunidad_id:
                    return JsonResponse({
                        'success': False,
                        'error': 'La colección padre debe pertenecer a la misma comunidad'
                    }, status=400)
                # Evitar referencia circular
                if coleccion_padre.id == coleccion_padre_id and 'id' in data and data.get('id'):
                    if int(coleccion_padre.id) == int(data.get('id')):
                        return JsonResponse({
                            'success': False,
                            'error': 'Una colección no puede ser su propia padre'
                        }, status=400)
            except Coleccion.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'La colección padre no existe'
                }, status=400)
        
        # Crear la colección
        coleccion = Coleccion(
            nombre=nombre,
            slug=slug,
            descripcion=data.get('descripcion', '').strip() or None,
            comunidad=comunidad,
            coleccion_padre=coleccion_padre,
            administrador=administrador,
            politica_ingreso=data.get('politica_ingreso', 'abierto'),
            es_publica=data.get('es_publica', True),
            plantilla_metadatos=data.get('plantilla_metadatos') if data.get('plantilla_metadatos') else None,
        )
        
        coleccion.full_clean()
        coleccion.save()
        
        # Retornar los datos de la colección creada
        coleccion_dict = {
            'id': coleccion.id,
            'nombre': coleccion.nombre,
            'slug': coleccion.slug,
            'descripcion': coleccion.descripcion or '',
            'comunidad_id': coleccion.comunidad.id,
            'comunidad_nombre': coleccion.comunidad.nombre,
            'coleccion_padre_id': coleccion.coleccion_padre.id if coleccion.coleccion_padre else None,
            'coleccion_padre_nombre': coleccion.coleccion_padre.nombre if coleccion.coleccion_padre else '',
            'administrador_id': coleccion.administrador.id,
            'administrador_nombre': coleccion.administrador.get_full_name() or coleccion.administrador.username,
            'politica_ingreso': coleccion.politica_ingreso,
            'es_publica': coleccion.es_publica,
            'fecha_creacion': coleccion.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S'),
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Colección creada exitosamente',
            'data': coleccion_dict
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
            'error': f'Error al crear colección: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def coleccion_detail(request, coleccion_id):
    """Obtiene los detalles de una colección"""
    try:
        coleccion = get_object_or_404(Coleccion, id=coleccion_id)
        
        coleccion_dict = {
            'id': coleccion.id,
            'nombre': coleccion.nombre,
            'slug': coleccion.slug,
            'descripcion': coleccion.descripcion or '',
            'comunidad_id': coleccion.comunidad.id,
            'comunidad_nombre': coleccion.comunidad.nombre,
            'coleccion_padre_id': coleccion.coleccion_padre.id if coleccion.coleccion_padre else None,
            'coleccion_padre_nombre': coleccion.coleccion_padre.nombre if coleccion.coleccion_padre else '',
            'administrador_id': coleccion.administrador.id,
            'administrador_nombre': coleccion.administrador.get_full_name() or coleccion.administrador.username,
            'politica_ingreso': coleccion.politica_ingreso,
            'es_publica': coleccion.es_publica,
            'plantilla_metadatos': coleccion.plantilla_metadatos,
            'fecha_creacion': coleccion.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S'),
        }
        
        return JsonResponse({
            'success': True,
            'data': coleccion_dict
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener colección: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "PUT"])
def coleccion_update(request, coleccion_id):
    """Actualiza una colección"""
    try:
        coleccion = get_object_or_404(Coleccion, id=coleccion_id)
        
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
        
        # Validar comunidad
        comunidad_id = data.get('comunidad_id')
        if not comunidad_id:
            return JsonResponse({
                'success': False,
                'error': 'La comunidad es obligatoria'
            }, status=400)
        
        try:
            comunidad = Comunidad.objects.get(id=comunidad_id)
        except Comunidad.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'La comunidad no existe'
            }, status=400)
        
        # Validar administrador
        administrador_id = data.get('administrador_id')
        if not administrador_id:
            return JsonResponse({
                'success': False,
                'error': 'El administrador es obligatorio'
            }, status=400)
        
        try:
            administrador = User.objects.get(id=administrador_id)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'El usuario administrador no existe'
            }, status=400)
        
        # Generar slug si el nombre cambió
        nuevo_slug = slugify(nombre)
        if not nuevo_slug:
            return JsonResponse({
                'success': False,
                'error': 'No se pudo generar un slug válido desde el nombre'
            }, status=400)
        
        # Validar que el slug sea único dentro de la comunidad (excepto para esta colección)
        if Coleccion.objects.filter(slug=nuevo_slug, comunidad=comunidad).exclude(id=coleccion_id).exists():
            return JsonResponse({
                'success': False,
                'error': 'Ya existe otra colección con este nombre en esta comunidad'
            }, status=400)
        
        # Validar coleccion_padre si existe
        coleccion_padre_id = data.get('coleccion_padre_id')
        coleccion_padre = None
        if coleccion_padre_id:
            try:
                coleccion_padre = Coleccion.objects.get(id=coleccion_padre_id)
                # Verificar que pertenezca a la misma comunidad
                if coleccion_padre.comunidad.id != comunidad_id:
                    return JsonResponse({
                        'success': False,
                        'error': 'La colección padre debe pertenecer a la misma comunidad'
                    }, status=400)
                # Evitar referencia circular
                if coleccion_padre.id == coleccion_id:
                    return JsonResponse({
                        'success': False,
                        'error': 'Una colección no puede ser su propia padre'
                    }, status=400)
            except Coleccion.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'La colección padre no existe'
                }, status=400)
        
        # Actualizar los campos
        coleccion.nombre = nombre
        coleccion.slug = nuevo_slug
        coleccion.descripcion = data.get('descripcion', '').strip() or None
        coleccion.comunidad = comunidad
        coleccion.coleccion_padre = coleccion_padre
        coleccion.administrador = administrador
        coleccion.politica_ingreso = data.get('politica_ingreso', 'abierto')
        coleccion.es_publica = data.get('es_publica', True)
        coleccion.plantilla_metadatos = data.get('plantilla_metadatos') if data.get('plantilla_metadatos') else None
        
        coleccion.full_clean()
        coleccion.save()
        
        # Retornar los datos actualizados
        coleccion_dict = {
            'id': coleccion.id,
            'nombre': coleccion.nombre,
            'slug': coleccion.slug,
            'descripcion': coleccion.descripcion or '',
            'comunidad_id': coleccion.comunidad.id,
            'comunidad_nombre': coleccion.comunidad.nombre,
            'coleccion_padre_id': coleccion.coleccion_padre.id if coleccion.coleccion_padre else None,
            'coleccion_padre_nombre': coleccion.coleccion_padre.nombre if coleccion.coleccion_padre else '',
            'administrador_id': coleccion.administrador.id,
            'administrador_nombre': coleccion.administrador.get_full_name() or coleccion.administrador.username,
            'politica_ingreso': coleccion.politica_ingreso,
            'es_publica': coleccion.es_publica,
            'fecha_creacion': coleccion.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S'),
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Colección actualizada exitosamente',
            'data': coleccion_dict
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
            'error': f'Error al actualizar colección: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "DELETE"])
def coleccion_delete(request, coleccion_id):
    """Elimina una colección"""
    try:
        coleccion = get_object_or_404(Coleccion, id=coleccion_id)
        
        # Manejar tanto POST con _method como DELETE directo
        if request.method == 'POST':
            data = json.loads(request.body) if request.body else {}
            if data.get('_method') != 'DELETE':
                return JsonResponse({
                    'success': False,
                    'error': 'Método no permitido'
                }, status=405)
        
        # Verificar si hay documentos o subcolecciones usando esta colección
        if coleccion.subcolecciones.exists():
            return JsonResponse({
                'success': False,
                'error': 'No se puede eliminar esta colección porque tiene subcolecciones asociadas'
            }, status=400)
        
        from .models import Documento
        if Documento.objects.filter(coleccion=coleccion).exists():
            return JsonResponse({
                'success': False,
                'error': 'No se puede eliminar esta colección porque tiene documentos asociados'
            }, status=400)
        
        # Eliminar la colección
        coleccion_nombre = coleccion.nombre
        coleccion.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Colección "{coleccion_nombre}" eliminada exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al eliminar colección: {str(e)}'
        }, status=500)


# ========================================================================
# LICENCIAS
# ========================================================================

@login_required
@require_http_methods(["GET"])
def licencias_list(request):
    """Lista todas las licencias"""
    try:
        licencias = Licencia.objects.all().order_by('nombre')
        licencias_data = []
        
        for licencia in licencias:
            licencia_dict = {
                'id': licencia.id,
                'nombre': licencia.nombre,
                'codigo': licencia.codigo,
                'version': licencia.version or '',
                'url': licencia.url or '',
                'descripcion': licencia.descripcion or '',
                'permite_comercial': licencia.permite_comercial,
                'permite_modificacion': licencia.permite_modificacion,
                'requiere_attribucion': licencia.requiere_attribucion,
                'texto_completo': licencia.texto_completo or '',
            }
            licencias_data.append(licencia_dict)
        
        return JsonResponse({
            'success': True,
            'data': licencias_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener licencias: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def licencia_create(request):
    """Crea una nueva licencia"""
    try:
        data = json.loads(request.body)
        
        # Validar campos requeridos
        nombre = data.get('nombre', '').strip()
        if not nombre:
            return JsonResponse({
                'success': False,
                'error': 'El nombre es obligatorio'
            }, status=400)
        
        codigo = data.get('codigo', '').strip()
        if not codigo:
            return JsonResponse({
                'success': False,
                'error': 'El código es obligatorio'
            }, status=400)
        
        # Validar que el código sea único
        if Licencia.objects.filter(codigo=codigo).exists():
            return JsonResponse({
                'success': False,
                'error': 'Ya existe una licencia con este código'
            }, status=400)
        
        # Crear la licencia
        licencia = Licencia(
            nombre=nombre,
            codigo=codigo,
            version=data.get('version', '').strip() or None,
            url=data.get('url', '').strip() or None,
            descripcion=data.get('descripcion', '').strip() or None,
            permite_comercial=data.get('permite_comercial', False),
            permite_modificacion=data.get('permite_modificacion', False),
            requiere_attribucion=data.get('requiere_attribucion', True),
            texto_completo=data.get('texto_completo', '').strip() or None,
        )
        
        licencia.full_clean()
        licencia.save()
        
        # Retornar los datos de la licencia creada
        licencia_dict = {
            'id': licencia.id,
            'nombre': licencia.nombre,
            'codigo': licencia.codigo,
            'version': licencia.version or '',
            'url': licencia.url or '',
            'descripcion': licencia.descripcion or '',
            'permite_comercial': licencia.permite_comercial,
            'permite_modificacion': licencia.permite_modificacion,
            'requiere_attribucion': licencia.requiere_attribucion,
            'texto_completo': licencia.texto_completo or '',
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Licencia creada exitosamente',
            'data': licencia_dict
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
            'error': f'Error al crear licencia: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def licencia_detail(request, licencia_id):
    """Obtiene los detalles de una licencia"""
    try:
        licencia = get_object_or_404(Licencia, id=licencia_id)
        
        licencia_dict = {
            'id': licencia.id,
            'nombre': licencia.nombre,
            'codigo': licencia.codigo,
            'version': licencia.version or '',
            'url': licencia.url or '',
            'descripcion': licencia.descripcion or '',
            'permite_comercial': licencia.permite_comercial,
            'permite_modificacion': licencia.permite_modificacion,
            'requiere_attribucion': licencia.requiere_attribucion,
            'texto_completo': licencia.texto_completo or '',
        }
        
        return JsonResponse({
            'success': True,
            'data': licencia_dict
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener licencia: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "PUT"])
def licencia_update(request, licencia_id):
    """Actualiza una licencia"""
    try:
        licencia = get_object_or_404(Licencia, id=licencia_id)
        
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
        
        codigo = data.get('codigo', '').strip()
        if not codigo:
            return JsonResponse({
                'success': False,
                'error': 'El código es obligatorio'
            }, status=400)
        
        # Validar que el código sea único (excepto para esta licencia)
        if Licencia.objects.filter(codigo=codigo).exclude(id=licencia_id).exists():
            return JsonResponse({
                'success': False,
                'error': 'Ya existe otra licencia con este código'
            }, status=400)
        
        # Actualizar los campos
        licencia.nombre = nombre
        licencia.codigo = codigo
        licencia.version = data.get('version', '').strip() or None
        licencia.url = data.get('url', '').strip() or None
        licencia.descripcion = data.get('descripcion', '').strip() or None
        licencia.permite_comercial = data.get('permite_comercial', False)
        licencia.permite_modificacion = data.get('permite_modificacion', False)
        licencia.requiere_attribucion = data.get('requiere_attribucion', True)
        licencia.texto_completo = data.get('texto_completo', '').strip() or None
        
        licencia.full_clean()
        licencia.save()
        
        # Retornar los datos actualizados
        licencia_dict = {
            'id': licencia.id,
            'nombre': licencia.nombre,
            'codigo': licencia.codigo,
            'version': licencia.version or '',
            'url': licencia.url or '',
            'descripcion': licencia.descripcion or '',
            'permite_comercial': licencia.permite_comercial,
            'permite_modificacion': licencia.permite_modificacion,
            'requiere_attribucion': licencia.requiere_attribucion,
            'texto_completo': licencia.texto_completo or '',
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Licencia actualizada exitosamente',
            'data': licencia_dict
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
            'error': f'Error al actualizar licencia: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "DELETE"])
def licencia_delete(request, licencia_id):
    """Elimina una licencia"""
    try:
        licencia = get_object_or_404(Licencia, id=licencia_id)
        
        # Manejar tanto POST con _method como DELETE directo
        if request.method == 'POST':
            data = json.loads(request.body) if request.body else {}
            if data.get('_method') != 'DELETE':
                return JsonResponse({
                    'success': False,
                    'error': 'Método no permitido'
                }, status=405)
        
        # Verificar si hay documentos usando esta licencia
        from .models import Documento
        if Documento.objects.filter(licencia=licencia).exists():
            return JsonResponse({
                'success': False,
                'error': 'No se puede eliminar esta licencia porque hay documentos que la están usando'
            }, status=400)
        
        # Eliminar la licencia
        licencia_nombre = licencia.nombre
        licencia.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Licencia "{licencia_nombre}" eliminada exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al eliminar licencia: {str(e)}'
        }, status=500)


# ========================================================================
# DOCUMENTOS
# ========================================================================

def generar_handle():
    """Genera un handle único para un documento"""
    return f"hdl:{uuid.uuid4().hex[:8]}/{uuid.uuid4().hex[:8]}"


@login_required
@require_http_methods(["GET"])
def documentos_disponibles(request):
    """Lista documentos disponibles (sin proyecto asociado) para seleccionar al crear proyecto"""
    try:
        documentos = Documento.objects.filter(
            proyecto__isnull=True
        ).select_related('tipo_recurso', 'coleccion', 'creador', 'estado').order_by('-fecha_creacion')
        
        documentos_data = []
        for documento in documentos:
            # Verificar si tiene archivo principal
            tiene_archivo = False
            archivo_principal = None
            version_actual = documento.versiones.filter(es_version_actual=True).first()
            if version_actual:
                archivo_principal = version_actual.archivos.filter(es_archivo_principal=True).first()
                tiene_archivo = archivo_principal is not None
            
            documento_dict = {
                'id': documento.id,
                'handle': documento.handle or '',
                'titulo': documento.get_titulo(),
                'resumen': documento.get_resumen() or '',
                'tipo_recurso_id': documento.tipo_recurso.id if documento.tipo_recurso else None,
                'tipo_recurso_nombre': documento.tipo_recurso.nombre if documento.tipo_recurso else '',
                'coleccion_id': documento.coleccion.id if documento.coleccion else None,
                'coleccion_nombre': documento.coleccion.nombre if documento.coleccion else '',
                'creador_id': documento.creador.id,
                'creador_nombre': documento.creador.get_full_name() or documento.creador.username,
                'estado_id': documento.estado.id if documento.estado else None,
                'estado_nombre': documento.estado.nombre if documento.estado else '',
                'tiene_archivo': tiene_archivo,
                'archivo_nombre': archivo_principal.nombre_original if archivo_principal else None,
                'fecha_creacion': documento.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S') if documento.fecha_creacion else None,
            }
            documentos_data.append(documento_dict)
        
        return JsonResponse({
            'success': True,
            'data': documentos_data,
            'total': len(documentos_data)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al listar documentos disponibles: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def documentos_list(request):
    """Lista todos los documentos"""
    try:
        documentos = Documento.objects.select_related(
            'tipo_recurso', 'coleccion', 'creador', 'estado', 'licencia', 'proyecto'
        ).prefetch_related('categorias', 'etiquetas').all().order_by('-fecha_creacion')
        
        documentos_data = []
        
        for documento in documentos:
            # Usar get_titulo() y get_resumen() que manejan el caso de proyecto asociado
            titulo = documento.get_titulo() if hasattr(documento, 'get_titulo') else (documento.titulo or f'Documento #{documento.id}')
            resumen = documento.get_resumen() if hasattr(documento, 'get_resumen') else (documento.resumen or '')
            
            documento_dict = {
                'id': documento.id,
                'handle': documento.handle or '',
                'titulo': titulo,
                'resumen': resumen,
                'proyecto_id': documento.proyecto.id if documento.proyecto else None,
                'proyecto_titulo': documento.proyecto.titulo if documento.proyecto else '',
                'tipo_recurso_id': documento.tipo_recurso.id if documento.tipo_recurso else None,
                'tipo_recurso_nombre': documento.tipo_recurso.nombre if documento.tipo_recurso else '',
                'coleccion_id': documento.coleccion.id if documento.coleccion else None,
                'coleccion_nombre': documento.coleccion.nombre if documento.coleccion else '',
                'comunidad_nombre': documento.coleccion.comunidad.nombre if documento.coleccion and documento.coleccion.comunidad else '',
                'creador_id': documento.creador.id,
                'creador_nombre': documento.creador.get_full_name() or documento.creador.username,
                'estado_id': documento.estado.id if documento.estado else None,
                'estado_nombre': documento.estado.nombre if documento.estado else '',
                'idioma': documento.idioma,
                'fecha_publicacion': documento.fecha_publicacion.strftime('%Y-%m-%d') if documento.fecha_publicacion else None,
                'fecha_aceptacion': documento.fecha_aceptacion.strftime('%Y-%m-%d') if documento.fecha_aceptacion else None,
                'visibilidad': documento.visibilidad,
                'version_actual': documento.version_actual,
                'doi': documento.doi or '',
                'isbn': documento.isbn or '',
                'issn': documento.issn or '',
                'licencia_id': documento.licencia.id if documento.licencia else None,
                'licencia_nombre': documento.licencia.nombre if documento.licencia else '',
                'palabras_clave': documento.palabras_clave or '',
                'fecha_creacion': documento.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S') if documento.fecha_creacion else '',
                'categorias': [{'id': c.id, 'nombre': c.nombre} for c in documento.categorias.all()],
                'etiquetas': [{'id': e.id, 'nombre': e.nombre} for e in documento.etiquetas.all()],
            }
            documentos_data.append(documento_dict)
        
        return JsonResponse({
            'success': True,
            'data': documentos_data
        })
        
    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener documentos: {str(e)}',
            'traceback': traceback.format_exc() if request.user.is_superuser else None
        }, status=500)


@login_required
@require_http_methods(["GET"])
def categorias_for_select(request):
    """Obtiene las categorías para usar en selects"""
    try:
        categorias = Categoria.objects.all().order_by('nombre')
        categorias_data = [{'id': c.id, 'nombre': c.nombre, 'ruta_completa': c.ruta_completa or c.nombre} for c in categorias]
        
        return JsonResponse({
            'success': True,
            'data': categorias_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener categorías: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def etiquetas_for_select(request):
    """Obtiene las etiquetas para usar en selects"""
    try:
        etiquetas = Etiqueta.objects.all().order_by('nombre')
        etiquetas_data = [{'id': e.id, 'nombre': e.nombre, 'color': e.color or '#007bff'} for e in etiquetas]
        
        return JsonResponse({
            'success': True,
            'data': etiquetas_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener etiquetas: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def tipos_recurso_for_select(request):
    """Obtiene los tipos de recurso para usar en selects"""
    try:
        tipos = TipoRecurso.objects.all().order_by('nombre')
        tipos_data = [{'id': t.id, 'nombre': t.nombre} for t in tipos]
        
        return JsonResponse({
            'success': True,
            'data': tipos_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener tipos de recurso: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def estados_documento_for_select(request):
    """Obtiene los estados de documento para usar en selects"""
    try:
        estados = EstadoDocumento.objects.all().order_by('orden', 'nombre')
        estados_data = [{'id': e.id, 'nombre': e.nombre} for e in estados]
        
        return JsonResponse({
            'success': True,
            'data': estados_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener estados de documento: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def licencias_for_select(request):
    """Obtiene las licencias para usar en selects"""
    try:
        licencias = Licencia.objects.all().order_by('nombre')
        licencias_data = [{'id': l.id, 'nombre': l.nombre, 'codigo': l.codigo} for l in licencias]
        
        return JsonResponse({
            'success': True,
            'data': licencias_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener licencias: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
@transaction.atomic
def documento_create(request):
    """Crea un nuevo documento con opción de subir archivo PDF"""
    try:
        # Manejar tanto JSON como FormData (con archivo)
        if request.FILES:
            # Si hay archivos, los datos vienen en request.POST
            data = request.POST.copy()
            # Convertir campos JSON si vienen como strings
            for key in ['categorias_ids', 'etiquetas_ids', 'temas', 'campos_personalizados', 'metadata_completa']:
                if key in data and isinstance(data[key], str):
                    try:
                        data[key] = json.loads(data[key])
                    except:
                        pass
        else:
            # Si no hay archivos, los datos vienen en request.body como JSON
            data = json.loads(request.body)
        
        # Validar proyecto (opcional pero recomendado)
        proyecto_id = data.get('proyecto_id')
        proyecto = None
        if proyecto_id:
            try:
                from proyectos.models import Proyecto
                proyecto = Proyecto.objects.get(id=proyecto_id)
                # Si hay proyecto, verificar que no tenga ya un documento
                if hasattr(proyecto, 'documento') and proyecto.documento:
                    return JsonResponse({
                        'success': False,
                        'error': 'Este proyecto ya tiene un documento asociado'
                    }, status=400)
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'Error al obtener proyecto: {str(e)}'
                }, status=400)
        
        # Validar campos requeridos
        # Si hay proyecto, el título es opcional (viene del proyecto)
        # Si no hay proyecto, el título es opcional pero recomendado
        titulo = data.get('titulo', '').strip() or None
        if not titulo and not proyecto:
            # Si no hay proyecto ni título, generar uno por defecto
            titulo = f'Documento #{Documento.objects.count() + 1}'
        
        # Validar tipo_recurso (opcional)
        tipo_recurso_id = data.get('tipo_recurso_id')
        tipo_recurso = None
        if tipo_recurso_id:
            try:
                tipo_recurso = TipoRecurso.objects.get(id=tipo_recurso_id)
            except TipoRecurso.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'El tipo de recurso no existe'
                }, status=400)
        
        # Validar coleccion (opcional)
        coleccion_id = data.get('coleccion_id')
        coleccion = None
        if coleccion_id:
            try:
                coleccion = Coleccion.objects.get(id=coleccion_id)
            except Coleccion.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'La colección no existe'
                }, status=400)
        
        # Validar estado (opcional)
        estado_id = data.get('estado_id')
        estado = None
        if estado_id:
            try:
                estado = EstadoDocumento.objects.get(id=estado_id)
            except EstadoDocumento.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'El estado no existe'
                }, status=400)
        
        # Validar licencia (opcional)
        licencia_id = data.get('licencia_id')
        licencia = None
        if licencia_id:
            try:
                licencia = Licencia.objects.get(id=licencia_id)
            except Licencia.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'La licencia no existe'
                }, status=400)
        
        # Generar handle único
        handle = data.get('handle', '').strip()
        if not handle:
            handle = generar_handle()
        else:
            # Validar que el handle sea único
            if Documento.objects.filter(handle=handle).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Ya existe un documento con este handle'
                }, status=400)
        
        # Validar DOI único si se proporciona
        doi = data.get('doi', '').strip() or None
        if doi and Documento.objects.filter(doi=doi).exists():
            return JsonResponse({
                'success': False,
                'error': 'Ya existe un documento con este DOI'
            }, status=400)
        
        # Parsear fechas
        fecha_publicacion = None
        fecha_aceptacion = None
        fecha_publicacion_disponible = None
        
        if data.get('fecha_publicacion'):
            try:
                fecha_publicacion = datetime.strptime(data.get('fecha_publicacion'), '%Y-%m-%d').date()
            except:
                pass
        
        if data.get('fecha_aceptacion'):
            try:
                fecha_aceptacion = datetime.strptime(data.get('fecha_aceptacion'), '%Y-%m-%d').date()
            except:
                pass
        
        if data.get('fecha_publicacion_disponible'):
            try:
                fecha_publicacion_disponible = datetime.strptime(
                    data.get('fecha_publicacion_disponible'), 
                    '%Y-%m-%d %H:%M:%S'
                )
            except:
                try:
                    fecha_publicacion_disponible = datetime.strptime(
                        data.get('fecha_publicacion_disponible'), 
                        '%Y-%m-%d'
                    )
                except:
                    pass
        
        # Parsear JSON fields
        temas = None
        campos_personalizados = None
        metadata_completa = None
        
        if data.get('temas'):
            try:
                if isinstance(data.get('temas'), str):
                    temas = json.loads(data.get('temas'))
                else:
                    temas = data.get('temas')
            except:
                temas = None
        
        if data.get('campos_personalizados'):
            try:
                if isinstance(data.get('campos_personalizados'), str):
                    campos_personalizados = json.loads(data.get('campos_personalizados'))
                else:
                    campos_personalizados = data.get('campos_personalizados')
            except:
                campos_personalizados = None
        
        if data.get('metadata_completa'):
            try:
                if isinstance(data.get('metadata_completa'), str):
                    metadata_completa = json.loads(data.get('metadata_completa'))
                else:
                    metadata_completa = data.get('metadata_completa')
            except:
                metadata_completa = None
        
        # Crear el documento
        documento = Documento(
            proyecto=proyecto,
            handle=handle or None,  # Puede ser None si no se proporciona
            titulo=titulo,
            resumen=data.get('resumen', '').strip() or None,
            tipo_recurso=tipo_recurso,
            coleccion=coleccion,
            creador=request.user,  # El usuario que crea el documento
            estado=estado,
            idioma=data.get('idioma', 'es'),
            fecha_publicacion=fecha_publicacion,
            fecha_aceptacion=fecha_aceptacion,
            fecha_publicacion_disponible=fecha_publicacion_disponible,
            visibilidad=data.get('visibilidad', 'publico'),
            version_actual=data.get('version_actual', 1),
            numero_acceso=data.get('numero_acceso', '').strip() or None,
            doi=doi,
            isbn=data.get('isbn', '').strip() or None,
            issn=data.get('issn', '').strip() or None,
            licencia=licencia,
            palabras_clave=data.get('palabras_clave', '').strip() or None,
            temas=temas,
            campos_personalizados=campos_personalizados,
            metadata_completa=metadata_completa,
        )
        
        documento.full_clean()
        documento.save()
        
        # Si se subió un archivo PDF, crear versión y archivo automáticamente
        if 'archivo' in request.FILES:
            uploaded_file = request.FILES['archivo']
            
            # Validar que sea un PDF
            if uploaded_file.content_type not in ['application/pdf', '']:
                if uploaded_file.content_type:
                    return JsonResponse({
                        'success': False,
                        'error': 'Solo se permiten archivos PDF'
                    }, status=400)
            
            # Validar tamaño del archivo (máximo 100MB)
            max_size = 100 * 1024 * 1024  # 100MB
            if uploaded_file.size > max_size:
                return JsonResponse({
                    'success': False,
                    'error': f'El archivo es demasiado grande. Tamaño máximo: 100MB'
                }, status=400)
            
            # Calcular checksums
            md5_hash, sha256_hash = calcular_checksums(uploaded_file)
            
            # Crear versión inicial
            version = VersionDocumento.objects.create(
                documento=documento,
                numero_version=1,
                creado_por=request.user,
                es_version_actual=True
            )
            
            # Obtener extensión del archivo
            nombre_archivo = uploaded_file.name
            extension = os.path.splitext(nombre_archivo)[1].lower().lstrip('.')
            
            # Crear archivo
            archivo = Archivo.objects.create(
                version=version,
                archivo=uploaded_file,
                nombre_original=nombre_archivo,
                tipo_mime=uploaded_file.content_type or 'application/pdf',
                tamaño_bytes=uploaded_file.size,
                checksum_md5=md5_hash,
                checksum_sha256=sha256_hash,
                es_archivo_principal=True,
                formato=extension
            )
        
        # Asignar categorías
        categorias_ids = data.get('categorias_ids', [])
        if categorias_ids:
            try:
                if isinstance(categorias_ids, str):
                    categorias_ids = json.loads(categorias_ids)
                categorias = Categoria.objects.filter(id__in=categorias_ids)
                documento.categorias.set(categorias)
            except:
                pass
        
        # Asignar etiquetas
        etiquetas_ids = data.get('etiquetas_ids', [])
        if etiquetas_ids:
            try:
                if isinstance(etiquetas_ids, str):
                    etiquetas_ids = json.loads(etiquetas_ids)
                etiquetas = Etiqueta.objects.filter(id__in=etiquetas_ids)
                documento.etiquetas.set(etiquetas)
            except:
                pass
        
        # Retornar los datos del documento creado
        documento.refresh_from_db()
        titulo_ret = documento.get_titulo() if hasattr(documento, 'get_titulo') else (documento.titulo or f'Documento #{documento.id}')
        resumen_ret = documento.get_resumen() if hasattr(documento, 'get_resumen') else (documento.resumen or '')
        
        documento_dict = {
            'id': documento.id,
            'handle': documento.handle or '',
            'titulo': titulo_ret,
            'resumen': resumen_ret,
            'proyecto_id': documento.proyecto.id if documento.proyecto else None,
            'proyecto_titulo': documento.proyecto.titulo if documento.proyecto else '',
            'tipo_recurso_id': documento.tipo_recurso.id if documento.tipo_recurso else None,
            'tipo_recurso_nombre': documento.tipo_recurso.nombre if documento.tipo_recurso else '',
            'coleccion_id': documento.coleccion.id if documento.coleccion else None,
            'coleccion_nombre': documento.coleccion.nombre if documento.coleccion else '',
            'creador_id': documento.creador.id,
            'creador_nombre': documento.creador.get_full_name() or documento.creador.username,
            'estado_id': documento.estado.id if documento.estado else None,
            'estado_nombre': documento.estado.nombre if documento.estado else '',
            'idioma': documento.idioma,
            'fecha_publicacion': documento.fecha_publicacion.strftime('%Y-%m-%d') if documento.fecha_publicacion else None,
            'fecha_aceptacion': documento.fecha_aceptacion.strftime('%Y-%m-%d') if documento.fecha_aceptacion else None,
            'visibilidad': documento.visibilidad,
            'version_actual': documento.version_actual,
            'doi': documento.doi or '',
            'isbn': documento.isbn or '',
            'issn': documento.issn or '',
            'licencia_id': documento.licencia.id if documento.licencia else None,
            'licencia_nombre': documento.licencia.nombre if documento.licencia else '',
            'palabras_clave': documento.palabras_clave or '',
            'categorias': [{'id': c.id, 'nombre': c.nombre} for c in documento.categorias.all()],
            'etiquetas': [{'id': e.id, 'nombre': e.nombre} for e in documento.etiquetas.all()],
            'fecha_creacion': documento.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S') if documento.fecha_creacion else '',
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Documento creado exitosamente',
            'data': documento_dict
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
            'error': f'Error al crear documento: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def documento_detail(request, documento_id):
    """Obtiene los detalles de un documento"""
    try:
        documento = get_object_or_404(
            Documento.objects.select_related(
                'tipo_recurso', 'coleccion', 'creador', 'estado', 'licencia', 'proyecto'
            ).prefetch_related('categorias', 'etiquetas'),
            id=documento_id
        )
        
        # Usar get_titulo() y get_resumen() que manejan el caso de proyecto asociado
        titulo = documento.get_titulo() if hasattr(documento, 'get_titulo') else (documento.titulo or f'Documento #{documento.id}')
        resumen = documento.get_resumen() if hasattr(documento, 'get_resumen') else (documento.resumen or '')
        
        documento_dict = {
            'id': documento.id,
            'handle': documento.handle or '',
            'titulo': titulo,
            'resumen': resumen,
            'proyecto_id': documento.proyecto.id if documento.proyecto else None,
            'proyecto_titulo': documento.proyecto.titulo if documento.proyecto else '',
            'tipo_recurso_id': documento.tipo_recurso.id if documento.tipo_recurso else None,
            'tipo_recurso_nombre': documento.tipo_recurso.nombre if documento.tipo_recurso else '',
            'coleccion_id': documento.coleccion.id if documento.coleccion else None,
            'coleccion_nombre': documento.coleccion.nombre if documento.coleccion else '',
            'creador_id': documento.creador.id,
            'creador_nombre': documento.creador.get_full_name() or documento.creador.username,
            'estado_id': documento.estado.id if documento.estado else None,
            'estado_nombre': documento.estado.nombre if documento.estado else '',
            'idioma': documento.idioma,
            'fecha_publicacion': documento.fecha_publicacion.strftime('%Y-%m-%d') if documento.fecha_publicacion else None,
            'fecha_aceptacion': documento.fecha_aceptacion.strftime('%Y-%m-%d') if documento.fecha_aceptacion else None,
            'fecha_publicacion_disponible': documento.fecha_publicacion_disponible.strftime('%Y-%m-%d %H:%M:%S') if documento.fecha_publicacion_disponible else None,
            'visibilidad': documento.visibilidad,
            'version_actual': documento.version_actual,
            'numero_acceso': documento.numero_acceso or '',
            'doi': documento.doi or '',
            'isbn': documento.isbn or '',
            'issn': documento.issn or '',
            'licencia_id': documento.licencia.id if documento.licencia else None,
            'licencia_nombre': documento.licencia.nombre if documento.licencia else '',
            'palabras_clave': documento.palabras_clave or '',
            'temas': documento.temas,
            'campos_personalizados': documento.campos_personalizados,
            'metadata_completa': documento.metadata_completa,
            'categorias': [{'id': c.id, 'nombre': c.nombre} for c in documento.categorias.all()],
            'etiquetas': [{'id': e.id, 'nombre': e.nombre} for e in documento.etiquetas.all()],
            'fecha_creacion': documento.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S') if documento.fecha_creacion else '',
            'fecha_actualizacion': documento.fecha_actualizacion.strftime('%Y-%m-%d %H:%M:%S') if documento.fecha_actualizacion else '',
        }
        
        return JsonResponse({
            'success': True,
            'data': documento_dict
        })
        
    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener documento: {str(e)}',
            'traceback': traceback.format_exc() if request.user.is_superuser else None
        }, status=500)


@login_required
@require_http_methods(["POST", "PUT"])
@transaction.atomic
def documento_update(request, documento_id):
    """Actualiza un documento"""
    try:
        documento = get_object_or_404(Documento, id=documento_id)
        
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
        
        # Validar tipo_recurso
        tipo_recurso_id = data.get('tipo_recurso_id')
        if not tipo_recurso_id:
            return JsonResponse({
                'success': False,
                'error': 'El tipo de recurso es obligatorio'
            }, status=400)
        
        try:
            tipo_recurso = TipoRecurso.objects.get(id=tipo_recurso_id)
        except TipoRecurso.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'El tipo de recurso no existe'
            }, status=400)
        
        # Validar coleccion
        coleccion_id = data.get('coleccion_id')
        if not coleccion_id:
            return JsonResponse({
                'success': False,
                'error': 'La colección es obligatoria'
            }, status=400)
        
        try:
            coleccion = Coleccion.objects.get(id=coleccion_id)
        except Coleccion.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'La colección no existe'
            }, status=400)
        
        # Validar estado
        estado_id = data.get('estado_id')
        if not estado_id:
            return JsonResponse({
                'success': False,
                'error': 'El estado es obligatorio'
            }, status=400)
        
        try:
            estado = EstadoDocumento.objects.get(id=estado_id)
        except EstadoDocumento.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'El estado no existe'
            }, status=400)
        
        # Validar licencia (opcional)
        licencia_id = data.get('licencia_id')
        licencia = None
        if licencia_id:
            try:
                licencia = Licencia.objects.get(id=licencia_id)
            except Licencia.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'La licencia no existe'
                }, status=400)
        
        # Validar handle único si cambió
        handle = data.get('handle', '').strip()
        if not handle:
            handle = documento.handle  # Mantener el handle existente
        else:
            if handle != documento.handle and Documento.objects.filter(handle=handle).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Ya existe otro documento con este handle'
                }, status=400)
        
        # Validar DOI único si cambió
        doi = data.get('doi', '').strip() or None
        if doi and doi != documento.doi and Documento.objects.filter(doi=doi).exists():
            return JsonResponse({
                'success': False,
                'error': 'Ya existe otro documento con este DOI'
            }, status=400)
        
        # Parsear fechas
        fecha_publicacion = None
        fecha_aceptacion = None
        fecha_publicacion_disponible = None
        
        if data.get('fecha_publicacion'):
            try:
                fecha_publicacion = datetime.strptime(data.get('fecha_publicacion'), '%Y-%m-%d').date()
            except:
                pass
        elif data.get('fecha_publicacion') == '':
            fecha_publicacion = None
        
        if data.get('fecha_aceptacion'):
            try:
                fecha_aceptacion = datetime.strptime(data.get('fecha_aceptacion'), '%Y-%m-%d').date()
            except:
                pass
        elif data.get('fecha_aceptacion') == '':
            fecha_aceptacion = None
        
        if data.get('fecha_publicacion_disponible'):
            try:
                fecha_publicacion_disponible = datetime.strptime(
                    data.get('fecha_publicacion_disponible'), 
                    '%Y-%m-%d %H:%M:%S'
                )
            except:
                try:
                    fecha_publicacion_disponible = datetime.strptime(
                        data.get('fecha_publicacion_disponible'), 
                        '%Y-%m-%d'
                    )
                except:
                    pass
        elif data.get('fecha_publicacion_disponible') == '':
            fecha_publicacion_disponible = None
        
        # Parsear JSON fields
        temas = documento.temas  # Mantener por defecto
        campos_personalizados = documento.campos_personalizados
        metadata_completa = documento.metadata_completa
        
        if 'temas' in data:
            try:
                if isinstance(data.get('temas'), str):
                    if data.get('temas').strip():
                        temas = json.loads(data.get('temas'))
                    else:
                        temas = None
                else:
                    temas = data.get('temas')
            except:
                pass
        
        if 'campos_personalizados' in data:
            try:
                if isinstance(data.get('campos_personalizados'), str):
                    if data.get('campos_personalizados').strip():
                        campos_personalizados = json.loads(data.get('campos_personalizados'))
                    else:
                        campos_personalizados = None
                else:
                    campos_personalizados = data.get('campos_personalizados')
            except:
                pass
        
        if 'metadata_completa' in data:
            try:
                if isinstance(data.get('metadata_completa'), str):
                    if data.get('metadata_completa').strip():
                        metadata_completa = json.loads(data.get('metadata_completa'))
                    else:
                        metadata_completa = None
                else:
                    metadata_completa = data.get('metadata_completa')
            except:
                pass
        
        # Actualizar los campos
        documento.handle = handle
        documento.titulo = titulo
        documento.resumen = data.get('resumen', '').strip() or None
        documento.tipo_recurso = tipo_recurso
        documento.coleccion = coleccion
        documento.estado = estado
        documento.idioma = data.get('idioma', 'es')
        documento.fecha_publicacion = fecha_publicacion
        documento.fecha_aceptacion = fecha_aceptacion
        documento.fecha_publicacion_disponible = fecha_publicacion_disponible
        documento.visibilidad = data.get('visibilidad', 'publico')
        documento.version_actual = data.get('version_actual', documento.version_actual)
        documento.numero_acceso = data.get('numero_acceso', '').strip() or None
        documento.doi = doi
        documento.isbn = data.get('isbn', '').strip() or None
        documento.issn = data.get('issn', '').strip() or None
        documento.licencia = licencia
        documento.palabras_clave = data.get('palabras_clave', '').strip() or None
        documento.temas = temas
        documento.campos_personalizados = campos_personalizados
        documento.metadata_completa = metadata_completa
        
        documento.full_clean()
        documento.save()
        
        # Actualizar categorías
        if 'categorias_ids' in data:
            categorias_ids = data.get('categorias_ids', [])
            try:
                if isinstance(categorias_ids, str):
                    categorias_ids = json.loads(categorias_ids) if categorias_ids.strip() else []
                if categorias_ids:
                    categorias = Categoria.objects.filter(id__in=categorias_ids)
                    documento.categorias.set(categorias)
                else:
                    documento.categorias.clear()
            except:
                pass
        
        # Actualizar etiquetas
        if 'etiquetas_ids' in data:
            etiquetas_ids = data.get('etiquetas_ids', [])
            try:
                if isinstance(etiquetas_ids, str):
                    etiquetas_ids = json.loads(etiquetas_ids) if etiquetas_ids.strip() else []
                if etiquetas_ids:
                    etiquetas = Etiqueta.objects.filter(id__in=etiquetas_ids)
                    documento.etiquetas.set(etiquetas)
                else:
                    documento.etiquetas.clear()
            except:
                pass
        
        # Retornar los datos actualizados
        documento.refresh_from_db()
        documento_dict = {
            'id': documento.id,
            'handle': documento.handle,
            'titulo': documento.titulo,
            'resumen': documento.resumen or '',
            'tipo_recurso_id': documento.tipo_recurso.id,
            'tipo_recurso_nombre': documento.tipo_recurso.nombre,
            'coleccion_id': documento.coleccion.id,
            'coleccion_nombre': documento.coleccion.nombre,
            'creador_id': documento.creador.id,
            'creador_nombre': documento.creador.get_full_name() or documento.creador.username,
            'estado_id': documento.estado.id,
            'estado_nombre': documento.estado.nombre,
            'idioma': documento.idioma,
            'fecha_publicacion': documento.fecha_publicacion.strftime('%Y-%m-%d') if documento.fecha_publicacion else None,
            'fecha_aceptacion': documento.fecha_aceptacion.strftime('%Y-%m-%d') if documento.fecha_aceptacion else None,
            'visibilidad': documento.visibilidad,
            'version_actual': documento.version_actual,
            'doi': documento.doi or '',
            'isbn': documento.isbn or '',
            'issn': documento.issn or '',
            'licencia_id': documento.licencia.id if documento.licencia else None,
            'licencia_nombre': documento.licencia.nombre if documento.licencia else '',
            'palabras_clave': documento.palabras_clave or '',
            'categorias': [{'id': c.id, 'nombre': c.nombre} for c in documento.categorias.all()],
            'etiquetas': [{'id': e.id, 'nombre': e.nombre} for e in documento.etiquetas.all()],
            'fecha_creacion': documento.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S'),
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Documento actualizado exitosamente',
            'data': documento_dict
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
            'error': f'Error al actualizar documento: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "DELETE"])
def documento_delete(request, documento_id):
    """Elimina un documento"""
    try:
        documento = get_object_or_404(Documento, id=documento_id)
        
        # Manejar tanto POST con _method como DELETE directo
        if request.method == 'POST':
            data = json.loads(request.body) if request.body else {}
            if data.get('_method') != 'DELETE':
                return JsonResponse({
                    'success': False,
                    'error': 'Método no permitido'
                }, status=405)
        
        # Verificar si hay versiones o archivos asociados (se eliminarán en cascada)
        # Podríamos agregar una validación aquí si es necesario
        
        # Eliminar el documento (esto eliminará en cascada versiones y archivos)
        documento_titulo = documento.titulo
        documento.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Documento "{documento_titulo}" eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al eliminar documento: {str(e)}'
        }, status=500)


# ========================================================================
# AUTORES
# ========================================================================

@login_required
@require_http_methods(["GET"])
def autores_list(request):
    """Lista todos los autores"""
    try:
        autores = Autor.objects.select_related('documento', 'usuario').all().order_by('documento', 'orden_autor')
        
        autores_data = []
        
        for autor in autores:
            autor_dict = {
                'id': autor.id,
                'documento_id': autor.documento.id,
                'documento_titulo': autor.documento.titulo,
                'usuario_id': autor.usuario.id if autor.usuario else None,
                'usuario_nombre': autor.usuario.get_full_name() or autor.usuario.username if autor.usuario else None,
                'nombre': autor.nombre,
                'apellidos': autor.apellidos,
                'email': autor.email or '',
                'afiliacion': autor.afiliacion or '',
                'orcid_id': autor.orcid_id or '',
                'orden_autor': autor.orden_autor,
                'es_correspondiente': autor.es_correspondiente,
                'es_autor_principal': autor.es_autor_principal,
            }
            autores_data.append(autor_dict)
        
        return JsonResponse({
            'success': True,
            'data': autores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener autores: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def autores_por_documento(request, documento_id):
    """Obtiene los autores de un documento específico"""
    try:
        autores = Autor.objects.filter(documento_id=documento_id).select_related('usuario').order_by('orden_autor')
        autores_data = []
        
        for autor in autores:
            autor_dict = {
                'id': autor.id,
                'usuario_id': autor.usuario.id if autor.usuario else None,
                'usuario_nombre': autor.usuario.get_full_name() or autor.usuario.username if autor.usuario else None,
                'nombre': autor.nombre,
                'apellidos': autor.apellidos,
                'email': autor.email or '',
                'afiliacion': autor.afiliacion or '',
                'orcid_id': autor.orcid_id or '',
                'orden_autor': autor.orden_autor,
                'es_correspondiente': autor.es_correspondiente,
                'es_autor_principal': autor.es_autor_principal,
            }
            autores_data.append(autor_dict)
        
        return JsonResponse({
            'success': True,
            'data': autores_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener autores: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
@transaction.atomic
def autor_create(request):
    """Crea un nuevo autor"""
    try:
        data = json.loads(request.body)
        
        # Validar campos requeridos
        documento_id = data.get('documento_id')
        if not documento_id:
            return JsonResponse({
                'success': False,
                'error': 'El documento es obligatorio'
            }, status=400)
        
        try:
            documento = Documento.objects.get(id=documento_id)
        except Documento.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'El documento no existe'
            }, status=400)
        
        nombre = data.get('nombre', '').strip()
        apellidos = data.get('apellidos', '').strip()
        
        if not nombre or not apellidos:
            return JsonResponse({
                'success': False,
                'error': 'El nombre y los apellidos son obligatorios'
            }, status=400)
        
        # Validar usuario si se proporciona
        usuario_id = data.get('usuario_id')
        usuario = None
        if usuario_id:
            try:
                usuario = User.objects.get(id=usuario_id)
            except User.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'El usuario no existe'
                }, status=400)
        
        # Validar ORCID si se proporciona
        orcid_id = data.get('orcid_id', '').strip() or None
        if orcid_id and len(orcid_id) > 19:
            return JsonResponse({
                'success': False,
                'error': 'El ORCID ID no puede tener más de 19 caracteres'
            }, status=400)
        
        # Crear el autor
        autor = Autor(
            documento=documento,
            usuario=usuario,
            nombre=nombre,
            apellidos=apellidos,
            email=data.get('email', '').strip() or None,
            afiliacion=data.get('afiliacion', '').strip() or None,
            orcid_id=orcid_id,
            orden_autor=data.get('orden_autor', 1),
            es_correspondiente=data.get('es_correspondiente', False),
            es_autor_principal=data.get('es_autor_principal', False),
        )
        
        autor.full_clean()
        autor.save()
        
        # Retornar los datos del autor creado
        autor_dict = {
            'id': autor.id,
            'documento_id': autor.documento.id,
            'documento_titulo': autor.documento.titulo,
            'usuario_id': autor.usuario.id if autor.usuario else None,
            'usuario_nombre': autor.usuario.get_full_name() or autor.usuario.username if autor.usuario else None,
            'nombre': autor.nombre,
            'apellidos': autor.apellidos,
            'email': autor.email or '',
            'afiliacion': autor.afiliacion or '',
            'orcid_id': autor.orcid_id or '',
            'orden_autor': autor.orden_autor,
            'es_correspondiente': autor.es_correspondiente,
            'es_autor_principal': autor.es_autor_principal,
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Autor creado exitosamente',
            'data': autor_dict
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
            'error': f'Error al crear autor: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def autor_detail(request, autor_id):
    """Obtiene los detalles de un autor"""
    try:
        autor = get_object_or_404(Autor.objects.select_related('documento', 'usuario'), id=autor_id)
        
        autor_dict = {
            'id': autor.id,
            'documento_id': autor.documento.id,
            'documento_titulo': autor.documento.titulo,
            'usuario_id': autor.usuario.id if autor.usuario else None,
            'usuario_nombre': autor.usuario.get_full_name() or autor.usuario.username if autor.usuario else None,
            'nombre': autor.nombre,
            'apellidos': autor.apellidos,
            'email': autor.email or '',
            'afiliacion': autor.afiliacion or '',
            'orcid_id': autor.orcid_id or '',
            'orden_autor': autor.orden_autor,
            'es_correspondiente': autor.es_correspondiente,
            'es_autor_principal': autor.es_autor_principal,
        }
        
        return JsonResponse({
            'success': True,
            'data': autor_dict
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener autor: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "PUT"])
@transaction.atomic
def autor_update(request, autor_id):
    """Actualiza un autor"""
    try:
        autor = get_object_or_404(Autor, id=autor_id)
        
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
        
        # Validar documento
        documento_id = data.get('documento_id')
        if not documento_id:
            return JsonResponse({
                'success': False,
                'error': 'El documento es obligatorio'
            }, status=400)
        
        try:
            documento = Documento.objects.get(id=documento_id)
        except Documento.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'El documento no existe'
            }, status=400)
        
        nombre = data.get('nombre', '').strip()
        apellidos = data.get('apellidos', '').strip()
        
        if not nombre or not apellidos:
            return JsonResponse({
                'success': False,
                'error': 'El nombre y los apellidos son obligatorios'
            }, status=400)
        
        # Validar usuario si se proporciona
        usuario_id = data.get('usuario_id')
        usuario = None
        if usuario_id:
            try:
                usuario = User.objects.get(id=usuario_id)
            except User.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'El usuario no existe'
                }, status=400)
        
        # Validar ORCID si se proporciona
        orcid_id = data.get('orcid_id', '').strip() or None
        if orcid_id and len(orcid_id) > 19:
            return JsonResponse({
                'success': False,
                'error': 'El ORCID ID no puede tener más de 19 caracteres'
            }, status=400)
        
        # Actualizar los campos
        autor.documento = documento
        autor.usuario = usuario
        autor.nombre = nombre
        autor.apellidos = apellidos
        autor.email = data.get('email', '').strip() or None
        autor.afiliacion = data.get('afiliacion', '').strip() or None
        autor.orcid_id = orcid_id
        autor.orden_autor = data.get('orden_autor', autor.orden_autor)
        autor.es_correspondiente = data.get('es_correspondiente', False)
        autor.es_autor_principal = data.get('es_autor_principal', False)
        
        autor.full_clean()
        autor.save()
        
        # Retornar los datos actualizados
        autor.refresh_from_db()
        autor_dict = {
            'id': autor.id,
            'documento_id': autor.documento.id,
            'documento_titulo': autor.documento.titulo,
            'usuario_id': autor.usuario.id if autor.usuario else None,
            'usuario_nombre': autor.usuario.get_full_name() or autor.usuario.username if autor.usuario else None,
            'nombre': autor.nombre,
            'apellidos': autor.apellidos,
            'email': autor.email or '',
            'afiliacion': autor.afiliacion or '',
            'orcid_id': autor.orcid_id or '',
            'orden_autor': autor.orden_autor,
            'es_correspondiente': autor.es_correspondiente,
            'es_autor_principal': autor.es_autor_principal,
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Autor actualizado exitosamente',
            'data': autor_dict
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
            'error': f'Error al actualizar autor: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "DELETE"])
def autor_delete(request, autor_id):
    """Elimina un autor"""
    try:
        autor = get_object_or_404(Autor, id=autor_id)
        
        # Manejar tanto POST con _method como DELETE directo
        if request.method == 'POST':
            data = json.loads(request.body) if request.body else {}
            if data.get('_method') != 'DELETE':
                return JsonResponse({
                    'success': False,
                    'error': 'Método no permitido'
                }, status=405)
        
        # Eliminar el autor
        autor_nombre = f"{autor.nombre} {autor.apellidos}"
        autor.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Autor "{autor_nombre}" eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al eliminar autor: {str(e)}'
        }, status=500)


# ========================================================================
# COLABORADORES
# ========================================================================

@login_required
@require_http_methods(["GET"])
def colaboradores_list(request):
    """Lista todos los colaboradores"""
    try:
        colaboradores = Colaborador.objects.select_related('documento', 'usuario').all().order_by('documento', 'rol')
        
        colaboradores_data = []
        
        for colaborador in colaboradores:
            colaborador_dict = {
                'id': colaborador.id,
                'documento_id': colaborador.documento.id,
                'documento_titulo': colaborador.documento.titulo,
                'usuario_id': colaborador.usuario.id,
                'usuario_nombre': colaborador.usuario.get_full_name() or colaborador.usuario.username,
                'rol': colaborador.rol,
                'permisos': colaborador.permisos,
                'fecha_asignacion': colaborador.fecha_asignacion.strftime('%Y-%m-%d %H:%M:%S'),
            }
            colaboradores_data.append(colaborador_dict)
        
        return JsonResponse({
            'success': True,
            'data': colaboradores_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener colaboradores: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def colaboradores_por_documento(request, documento_id):
    """Obtiene los colaboradores de un documento específico"""
    try:
        colaboradores = Colaborador.objects.filter(documento_id=documento_id).select_related('usuario').order_by('rol')
        colaboradores_data = []
        
        for colaborador in colaboradores:
            colaborador_dict = {
                'id': colaborador.id,
                'usuario_id': colaborador.usuario.id,
                'usuario_nombre': colaborador.usuario.get_full_name() or colaborador.usuario.username,
                'rol': colaborador.rol,
                'permisos': colaborador.permisos,
                'fecha_asignacion': colaborador.fecha_asignacion.strftime('%Y-%m-%d %H:%M:%S'),
            }
            colaboradores_data.append(colaborador_dict)
        
        return JsonResponse({
            'success': True,
            'data': colaboradores_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener colaboradores: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
@transaction.atomic
def colaborador_create(request):
    """Crea un nuevo colaborador"""
    try:
        data = json.loads(request.body)
        
        # Validar campos requeridos
        documento_id = data.get('documento_id')
        if not documento_id:
            return JsonResponse({
                'success': False,
                'error': 'El documento es obligatorio'
            }, status=400)
        
        try:
            documento = Documento.objects.get(id=documento_id)
        except Documento.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'El documento no existe'
            }, status=400)
        
        usuario_id = data.get('usuario_id')
        if not usuario_id:
            return JsonResponse({
                'success': False,
                'error': 'El usuario es obligatorio'
            }, status=400)
        
        try:
            usuario = User.objects.get(id=usuario_id)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'El usuario no existe'
            }, status=400)
        
        rol = data.get('rol', '').strip()
        if not rol:
            return JsonResponse({
                'success': False,
                'error': 'El rol es obligatorio'
            }, status=400)
        
        # Validar que el rol sea válido
        roles_validos = [choice[0] for choice in Colaborador.ROL_CHOICES]
        if rol not in roles_validos:
            return JsonResponse({
                'success': False,
                'error': f'El rol debe ser uno de: {", ".join(roles_validos)}'
            }, status=400)
        
        # Validar que no exista ya un colaborador con el mismo usuario y documento
        if Colaborador.objects.filter(documento=documento, usuario=usuario).exists():
            return JsonResponse({
                'success': False,
                'error': 'Este usuario ya es colaborador de este documento'
            }, status=400)
        
        # Parsear permisos JSON
        permisos = None
        if data.get('permisos'):
            try:
                if isinstance(data.get('permisos'), str):
                    permisos = json.loads(data.get('permisos'))
                else:
                    permisos = data.get('permisos')
            except:
                permisos = None
        
        # Crear el colaborador
        colaborador = Colaborador(
            documento=documento,
            usuario=usuario,
            rol=rol,
            permisos=permisos,
        )
        
        colaborador.full_clean()
        colaborador.save()
        
        # Retornar los datos del colaborador creado
        colaborador_dict = {
            'id': colaborador.id,
            'documento_id': colaborador.documento.id,
            'documento_titulo': colaborador.documento.titulo,
            'usuario_id': colaborador.usuario.id,
            'usuario_nombre': colaborador.usuario.get_full_name() or colaborador.usuario.username,
            'rol': colaborador.rol,
            'permisos': colaborador.permisos,
            'fecha_asignacion': colaborador.fecha_asignacion.strftime('%Y-%m-%d %H:%M:%S'),
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Colaborador creado exitosamente',
            'data': colaborador_dict
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
            'error': f'Error al crear colaborador: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def colaborador_detail(request, colaborador_id):
    """Obtiene los detalles de un colaborador"""
    try:
        colaborador = get_object_or_404(Colaborador.objects.select_related('documento', 'usuario'), id=colaborador_id)
        
        colaborador_dict = {
            'id': colaborador.id,
            'documento_id': colaborador.documento.id,
            'documento_titulo': colaborador.documento.titulo,
            'usuario_id': colaborador.usuario.id,
            'usuario_nombre': colaborador.usuario.get_full_name() or colaborador.usuario.username,
            'rol': colaborador.rol,
            'permisos': colaborador.permisos,
            'fecha_asignacion': colaborador.fecha_asignacion.strftime('%Y-%m-%d %H:%M:%S'),
        }
        
        return JsonResponse({
            'success': True,
            'data': colaborador_dict
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener colaborador: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "PUT"])
@transaction.atomic
def colaborador_update(request, colaborador_id):
    """Actualiza un colaborador"""
    try:
        colaborador = get_object_or_404(Colaborador, id=colaborador_id)
        
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
        
        # Validar documento
        documento_id = data.get('documento_id')
        if not documento_id:
            return JsonResponse({
                'success': False,
                'error': 'El documento es obligatorio'
            }, status=400)
        
        try:
            documento = Documento.objects.get(id=documento_id)
        except Documento.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'El documento no existe'
            }, status=400)
        
        # Validar usuario
        usuario_id = data.get('usuario_id')
        if not usuario_id:
            return JsonResponse({
                'success': False,
                'error': 'El usuario es obligatorio'
            }, status=400)
        
        try:
            usuario = User.objects.get(id=usuario_id)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'El usuario no existe'
            }, status=400)
        
        # Validar rol
        rol = data.get('rol', '').strip()
        if not rol:
            return JsonResponse({
                'success': False,
                'error': 'El rol es obligatorio'
            }, status=400)
        
        # Validar que el rol sea válido
        roles_validos = [choice[0] for choice in Colaborador.ROL_CHOICES]
        if rol not in roles_validos:
            return JsonResponse({
                'success': False,
                'error': f'El rol debe ser uno de: {", ".join(roles_validos)}'
            }, status=400)
        
        # Validar que no exista ya otro colaborador con el mismo usuario y documento (excepto este)
        if Colaborador.objects.filter(documento=documento, usuario=usuario).exclude(id=colaborador_id).exists():
            return JsonResponse({
                'success': False,
                'error': 'Este usuario ya es colaborador de este documento'
            }, status=400)
        
        # Parsear permisos JSON
        permisos = colaborador.permisos  # Mantener por defecto
        if 'permisos' in data:
            try:
                if isinstance(data.get('permisos'), str):
                    if data.get('permisos').strip():
                        permisos = json.loads(data.get('permisos'))
                    else:
                        permisos = None
                else:
                    permisos = data.get('permisos')
            except:
                pass
        
        # Actualizar los campos
        colaborador.documento = documento
        colaborador.usuario = usuario
        colaborador.rol = rol
        colaborador.permisos = permisos
        
        colaborador.full_clean()
        colaborador.save()
        
        # Retornar los datos actualizados
        colaborador.refresh_from_db()
        colaborador_dict = {
            'id': colaborador.id,
            'documento_id': colaborador.documento.id,
            'documento_titulo': colaborador.documento.titulo,
            'usuario_id': colaborador.usuario.id,
            'usuario_nombre': colaborador.usuario.get_full_name() or colaborador.usuario.username,
            'rol': colaborador.rol,
            'permisos': colaborador.permisos,
            'fecha_asignacion': colaborador.fecha_asignacion.strftime('%Y-%m-%d %H:%M:%S'),
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Colaborador actualizado exitosamente',
            'data': colaborador_dict
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
            'error': f'Error al actualizar colaborador: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "DELETE"])
def colaborador_delete(request, colaborador_id):
    """Elimina un colaborador"""
    try:
        colaborador = get_object_or_404(Colaborador, id=colaborador_id)
        
        # Manejar tanto POST con _method como DELETE directo
        if request.method == 'POST':
            data = json.loads(request.body) if request.body else {}
            if data.get('_method') != 'DELETE':
                return JsonResponse({
                    'success': False,
                    'error': 'Método no permitido'
                }, status=405)
        
        # Eliminar el colaborador
        colaborador_nombre = colaborador.usuario.get_full_name() or colaborador.usuario.username
        colaborador.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Colaborador "{colaborador_nombre}" eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al eliminar colaborador: {str(e)}'
        }, status=500)


# ========================================================================
# ARCHIVOS (PDFs)
# ========================================================================

def calcular_checksums(archivo_file):
    """Calcula MD5 y SHA256 de un archivo"""
    md5_hash = hashlib.md5()
    sha256_hash = hashlib.sha256()
    
    # Leer el archivo en chunks para archivos grandes
    archivo_file.seek(0)  # Asegurar que estamos al inicio
    for chunk in archivo_file.chunks():
        md5_hash.update(chunk)
        sha256_hash.update(chunk)
    
    archivo_file.seek(0)  # Resetear al inicio para guardar
    return md5_hash.hexdigest(), sha256_hash.hexdigest()


@login_required
@require_http_methods(["GET"])
def archivos_list(request):
    """Lista todos los archivos - Soporta HTML y JSON"""
    try:
        archivos = Archivo.objects.select_related('version', 'version__documento', 'version__documento__proyecto').all().order_by('-fecha_subida')
        archivos_data = []
        
        for archivo in archivos:
            archivo_dict = {
                'id': archivo.id,
                'version_id': archivo.version.id,
                'version_numero': archivo.version.numero_version,
                'documento_id': archivo.version.documento.id,
                'documento_titulo': archivo.version.documento.get_titulo(),
                'proyecto_id': archivo.version.documento.proyecto.id if archivo.version.documento.proyecto else None,
                'proyecto_titulo': archivo.version.documento.proyecto.titulo if archivo.version.documento.proyecto else None,
                'nombre_original': archivo.nombre_original,
                'archivo_url': archivo.archivo.url if archivo.archivo else None,
                'tipo_mime': archivo.tipo_mime or '',
                'tamaño_bytes': archivo.tamaño_bytes,
                'tamaño_formateado': archivo.get_tamaño_formateado(),
                'checksum_md5': archivo.checksum_md5 or '',
                'checksum_sha256': archivo.checksum_sha256 or '',
                'es_archivo_principal': archivo.es_archivo_principal,
                'formato': archivo.formato or '',
                'numero_paginas': archivo.numero_paginas,
                'descripcion': archivo.descripcion or '',
                'fecha_subida': archivo.fecha_subida.isoformat() if archivo.fecha_subida else None,
            }
            archivos_data.append(archivo_dict)
        
        # Si es una petición AJAX o con Accept: application/json, retornar JSON
        if request.headers.get('Accept') == 'application/json' or request.GET.get('format') == 'json':
            return JsonResponse({
                'success': True,
                'data': archivos_data,
                'total': len(archivos_data)
            })
        
        # Si no, renderizar el template HTML (redirigir al template de repositorio)
        from django.shortcuts import redirect
        return redirect('repositorio:repositorio_index')
        
    except Exception as e:
        # Si es JSON, retornar error JSON
        if request.headers.get('Accept') == 'application/json' or request.GET.get('format') == 'json':
            return JsonResponse({
                'success': False,
                'error': f'Error al listar archivos: {str(e)}'
            }, status=500)
        # Si no, redirigir con error
        from django.contrib import messages
        messages.error(request, f'Error al listar archivos: {str(e)}')
        return redirect('repositorio:repositorio_index')


@login_required
@require_http_methods(["GET"])
def archivos_por_documento(request, documento_id):
    """Lista todos los archivos de un documento (todas sus versiones)"""
    try:
        documento = get_object_or_404(Documento, id=documento_id)
        
        # Obtener todas las versiones del documento
        versiones = VersionDocumento.objects.filter(documento=documento).order_by('-numero_version')
        
        archivos_data = []
        versiones_data = []
        
        for version in versiones:
            archivos_version = Archivo.objects.filter(version=version).order_by('-es_archivo_principal', 'fecha_subida')
            
            archivos_version_data = []
            for archivo in archivos_version:
                archivo_dict = {
                    'id': archivo.id,
                    'version_id': archivo.version.id,
                    'version_numero': archivo.version.numero_version,
                    'nombre_original': archivo.nombre_original,
                    'archivo_url': archivo.archivo.url if archivo.archivo else None,
                    'tipo_mime': archivo.tipo_mime or '',
                    'tamaño_bytes': archivo.tamaño_bytes,
                    'tamaño_formateado': archivo.get_tamaño_formateado(),
                    'checksum_md5': archivo.checksum_md5 or '',
                    'checksum_sha256': archivo.checksum_sha256 or '',
                    'es_archivo_principal': archivo.es_archivo_principal,
                    'formato': archivo.formato or '',
                    'numero_paginas': archivo.numero_paginas,
                    'descripcion': archivo.descripcion or '',
                    'fecha_subida': archivo.fecha_subida.isoformat() if archivo.fecha_subida else None,
                }
                archivos_version_data.append(archivo_dict)
                archivos_data.append(archivo_dict)
            
            versiones_data.append({
                'id': version.id,
                'numero_version': version.numero_version,
                'es_version_actual': version.es_version_actual,
                'notas_version': version.notas_version or '',
                'fecha_creacion': version.fecha_creacion.isoformat() if version.fecha_creacion else None,
                'archivos': archivos_version_data,
                'archivos_count': len(archivos_version_data)
            })
        
        return JsonResponse({
            'success': True,
            'data': archivos_data,
            'versiones': versiones_data,
            'documento': {
                'id': documento.id,
                'titulo': documento.get_titulo(),
                'handle': documento.handle or '',
            },
            'total': len(archivos_data)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al listar archivos del documento: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def archivos_por_version(request, version_id):
    """Lista los archivos de una versión específica"""
    try:
        version = get_object_or_404(VersionDocumento, id=version_id)
        archivos = Archivo.objects.filter(version=version).order_by('-es_archivo_principal', 'fecha_subida')
        archivos_data = []
        
        for archivo in archivos:
            archivo_dict = {
                'id': archivo.id,
                'version_id': archivo.version.id,
                'version_numero': archivo.version.numero_version,
                'documento_id': archivo.version.documento.id,
                'documento_titulo': archivo.version.documento.get_titulo(),
                'nombre_original': archivo.nombre_original,
                'archivo_url': archivo.archivo.url if archivo.archivo else None,
                'tipo_mime': archivo.tipo_mime or '',
                'tamaño_bytes': archivo.tamaño_bytes,
                'tamaño_formateado': archivo.get_tamaño_formateado(),
                'checksum_md5': archivo.checksum_md5 or '',
                'checksum_sha256': archivo.checksum_sha256 or '',
                'es_archivo_principal': archivo.es_archivo_principal,
                'formato': archivo.formato or '',
                'numero_paginas': archivo.numero_paginas,
                'descripcion': archivo.descripcion or '',
                'fecha_subida': archivo.fecha_subida.isoformat() if archivo.fecha_subida else None,
            }
            archivos_data.append(archivo_dict)
        
        return JsonResponse({
            'success': True,
            'data': archivos_data,
            'version': {
                'id': version.id,
                'numero_version': version.numero_version,
                'documento_id': version.documento.id,
                'documento_titulo': version.documento.get_titulo(),
            },
            'total': len(archivos_data)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al listar archivos de la versión: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
@transaction.atomic
def archivo_create(request):
    """Crea/Sube un nuevo archivo PDF a un documento o versión"""
    try:
        # Validar que se haya enviado un archivo
        if 'archivo' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'No se ha enviado ningún archivo'
            }, status=400)
        
        uploaded_file = request.FILES['archivo']
        
        # Validar que sea un PDF
        if uploaded_file.content_type not in ['application/pdf', '']:
            if uploaded_file.content_type:
                return JsonResponse({
                    'success': False,
                    'error': 'Solo se permiten archivos PDF'
                }, status=400)
        
        # Puede venir documento_id o version_id
        documento_id = request.POST.get('documento_id')
        version_id = request.POST.get('version_id')
        
        version = None
        
        # Si viene documento_id, crear o usar versión actual
        if documento_id:
            try:
                documento = Documento.objects.get(id=documento_id)
                # Buscar versión actual del documento
                version = documento.versiones.filter(es_version_actual=True).first()
                
                # Si no hay versión actual, crear una nueva
                if not version:
                    # Obtener el número de versión más alto
                    ultima_version = documento.versiones.order_by('-numero_version').first()
                    numero_version = (ultima_version.numero_version + 1) if ultima_version else 1
                    
                    version = VersionDocumento.objects.create(
                        documento=documento,
                        numero_version=numero_version,
                        creado_por=request.user,
                        es_version_actual=True
                    )
                    # Marcar otras versiones como no actuales
                    documento.versiones.exclude(id=version.id).update(es_version_actual=False)
            except Documento.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'El documento no existe'
                }, status=400)
        
        # Si viene version_id, usar esa versión
        elif version_id:
            try:
                version = VersionDocumento.objects.get(id=version_id)
            except VersionDocumento.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'La versión no existe'
                }, status=400)
        
        # Si no viene ni documento_id ni version_id, error
        else:
            return JsonResponse({
                'success': False,
                'error': 'Debe proporcionar documento_id o version_id'
            }, status=400)
        
        # Validar tamaño del archivo (opcional: máximo 100MB)
        max_size = 100 * 1024 * 1024  # 100MB
        if uploaded_file.size > max_size:
            return JsonResponse({
                'success': False,
                'error': f'El archivo es demasiado grande. Tamaño máximo: 100MB'
            }, status=400)
        
        # Calcular checksums
        md5_hash, sha256_hash = calcular_checksums(uploaded_file)
        
        # Determinar si es archivo principal
        es_archivo_principal = request.POST.get('es_archivo_principal', 'false').lower() == 'true'
        
        # Si se marca como principal, desmarcar otros archivos principales de esta versión
        if es_archivo_principal:
            Archivo.objects.filter(version=version, es_archivo_principal=True).update(es_archivo_principal=False)
        
        # Obtener extensión del archivo
        nombre_archivo = uploaded_file.name
        extension = os.path.splitext(nombre_archivo)[1].lower().lstrip('.')
        
        # Crear el archivo
        archivo = Archivo(
            version=version,
            archivo=uploaded_file,
            nombre_original=nombre_archivo,
            tipo_mime=uploaded_file.content_type or 'application/pdf',
            tamaño_bytes=uploaded_file.size,
            checksum_md5=md5_hash,
            checksum_sha256=sha256_hash,
            es_archivo_principal=es_archivo_principal,
            formato=extension,
            descripcion=request.POST.get('descripcion', '').strip() or None,
        )
        
        archivo.full_clean()
        archivo.save()
        
        # Retornar los datos del archivo creado
        archivo_dict = {
            'id': archivo.id,
            'version_id': archivo.version.id,
            'version_numero': archivo.version.numero_version,
            'documento_id': archivo.version.documento.id,
            'documento_titulo': archivo.version.documento.get_titulo(),
            'nombre_original': archivo.nombre_original,
            'archivo_url': archivo.archivo.url if archivo.archivo else None,
            'tipo_mime': archivo.tipo_mime or '',
            'tamaño_bytes': archivo.tamaño_bytes,
            'tamaño_formateado': archivo.get_tamaño_formateado(),
            'checksum_md5': archivo.checksum_md5 or '',
            'checksum_sha256': archivo.checksum_sha256 or '',
            'es_archivo_principal': archivo.es_archivo_principal,
            'formato': archivo.formato or '',
            'descripcion': archivo.descripcion or '',
            'fecha_subida': archivo.fecha_subida.isoformat() if archivo.fecha_subida else None,
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Archivo subido exitosamente',
            'data': archivo_dict
        })
        
    except ValidationError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al subir archivo: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def archivo_detail(request, archivo_id):
    """Obtiene los detalles de un archivo"""
    try:
        archivo = get_object_or_404(
            Archivo.objects.select_related('version', 'version__documento', 'version__documento__proyecto'),
            id=archivo_id
        )
        
        archivo_dict = {
            'id': archivo.id,
            'version_id': archivo.version.id,
            'version_numero': archivo.version.numero_version,
            'version_notas': archivo.version.notas_version or '',
            'documento_id': archivo.version.documento.id,
            'documento_titulo': archivo.version.documento.get_titulo(),
            'proyecto_id': archivo.version.documento.proyecto.id if archivo.version.documento.proyecto else None,
            'proyecto_titulo': archivo.version.documento.proyecto.titulo if archivo.version.documento.proyecto else None,
            'nombre_original': archivo.nombre_original,
            'archivo_url': archivo.archivo.url if archivo.archivo else None,
            'tipo_mime': archivo.tipo_mime or '',
            'tamaño_bytes': archivo.tamaño_bytes,
            'tamaño_formateado': archivo.get_tamaño_formateado(),
            'checksum_md5': archivo.checksum_md5 or '',
            'checksum_sha256': archivo.checksum_sha256 or '',
            'es_archivo_principal': archivo.es_archivo_principal,
            'formato': archivo.formato or '',
            'numero_paginas': archivo.numero_paginas,
            'descripcion': archivo.descripcion or '',
            'fecha_subida': archivo.fecha_subida.isoformat() if archivo.fecha_subida else None,
        }
        
        return JsonResponse({
            'success': True,
            'data': archivo_dict
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener archivo: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "PUT"])
@transaction.atomic
def archivo_update(request, archivo_id):
    """Actualiza un archivo (metadatos, no el archivo en sí)"""
    try:
        archivo = get_object_or_404(Archivo, id=archivo_id)
        
        # Manejar tanto POST con _method como PUT directo
        if request.method == 'POST':
            data = request.POST
        else:
            # Para PUT, los datos pueden venir en request.body o request.POST
            if request.body:
                try:
                    data = json.loads(request.body)
                except:
                    data = request.POST
            else:
                data = request.POST
        
        # Actualizar campos permitidos
        if 'descripcion' in data:
            archivo.descripcion = data.get('descripcion', '').strip() or None
        
        if 'es_archivo_principal' in data:
            es_archivo_principal = data.get('es_archivo_principal', 'false').lower() == 'true'
            archivo.es_archivo_principal = es_archivo_principal
            
            # Si se marca como principal, desmarcar otros archivos principales de esta versión
            if es_archivo_principal:
                Archivo.objects.filter(version=archivo.version, es_archivo_principal=True).exclude(id=archivo_id).update(es_archivo_principal=False)
        
        if 'numero_paginas' in data:
            try:
                archivo.numero_paginas = int(data.get('numero_paginas')) if data.get('numero_paginas') else None
            except (ValueError, TypeError):
                pass
        
        archivo.full_clean()
        archivo.save()
        
        # Retornar los datos actualizados
        archivo.refresh_from_db()
        archivo_dict = {
            'id': archivo.id,
            'version_id': archivo.version.id,
            'version_numero': archivo.version.numero_version,
            'documento_id': archivo.version.documento.id,
            'documento_titulo': archivo.version.documento.get_titulo(),
            'nombre_original': archivo.nombre_original,
            'archivo_url': archivo.archivo.url if archivo.archivo else None,
            'tipo_mime': archivo.tipo_mime or '',
            'tamaño_bytes': archivo.tamaño_bytes,
            'tamaño_formateado': archivo.get_tamaño_formateado(),
            'checksum_md5': archivo.checksum_md5 or '',
            'checksum_sha256': archivo.checksum_sha256 or '',
            'es_archivo_principal': archivo.es_archivo_principal,
            'formato': archivo.formato or '',
            'numero_paginas': archivo.numero_paginas,
            'descripcion': archivo.descripcion or '',
            'fecha_subida': archivo.fecha_subida.isoformat() if archivo.fecha_subida else None,
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Archivo actualizado exitosamente',
            'data': archivo_dict
        })
        
    except ValidationError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al actualizar archivo: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "DELETE"])
@transaction.atomic
def archivo_delete(request, archivo_id):
    """Elimina un archivo"""
    try:
        archivo = get_object_or_404(Archivo, id=archivo_id)
        
        # Manejar tanto POST con _method como DELETE directo
        if request.method == 'POST':
            data = json.loads(request.body) if request.body else {}
            if data.get('_method') != 'DELETE':
                return JsonResponse({
                    'success': False,
                    'error': 'Método no permitido'
                }, status=405)
        
        # Guardar información antes de eliminar
        nombre_archivo = archivo.nombre_original
        archivo_path = archivo.archivo.path if archivo.archivo else None
        
        # Eliminar el archivo
        archivo.delete()
        
        # Eliminar el archivo físico si existe
        if archivo_path and os.path.exists(archivo_path):
            try:
                os.remove(archivo_path)
            except Exception as e:
                # Log el error pero no fallar la operación
                pass
        
        return JsonResponse({
            'success': True,
            'message': f'Archivo "{nombre_archivo}" eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al eliminar archivo: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def archivo_download(request, archivo_id):
    """Descarga un archivo"""
    try:
        archivo = get_object_or_404(Archivo, id=archivo_id)
        
        if not archivo.archivo:
            return JsonResponse({
                'success': False,
                'error': 'El archivo no existe'
            }, status=404)
        
        # Verificar que el archivo físico existe
        if not archivo.archivo.storage.exists(archivo.archivo.name):
            return JsonResponse({
                'success': False,
                'error': 'El archivo físico no existe en el servidor'
            }, status=404)
        
        # Retornar el archivo para descarga
        response = FileResponse(
            archivo.archivo.open('rb'),
            as_attachment=True,
            filename=archivo.nombre_original
        )
        return response
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al descargar archivo: {str(e)}'
        }, status=500)
