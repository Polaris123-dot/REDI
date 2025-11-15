from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.forms.models import model_to_dict
import json
from .models import Categoria, Etiqueta


@login_required
@ensure_csrf_cookie
@require_http_methods(["GET"])
def index(request):
    """Vista principal de catalogación"""
    # Verificar permisos
    if not (request.user.has_perm('catalogacion.view_categoria') or 
            request.user.has_perm('catalogacion.view_etiqueta') or 
            request.user.is_superuser):
        messages.warning(request, 'No tienes permisos para acceder a catalogación.')
        return redirect('usuarios:panel')
    return render(request, 'catalogacion/index.html')


# ============================================================================
# VISTAS PARA CATEGORÍAS
# ============================================================================

@login_required
@require_http_methods(["GET"])
def categorias_list(request):
    """Lista todas las categorías en formato JSON"""
    categorias = Categoria.objects.all()
    categorias_data = []
    
    for categoria in categorias:
        categoria_dict = {
            'id': categoria.id,
            'nombre': categoria.nombre,
            'slug': categoria.slug,
            'descripcion': categoria.descripcion or '',
            'categoria_padre_id': categoria.categoria_padre.id if categoria.categoria_padre else None,
            'categoria_padre_nombre': categoria.categoria_padre.nombre if categoria.categoria_padre else None,
            'nivel': categoria.nivel,
            'ruta_completa': categoria.ruta_completa or categoria.nombre,
            'subcategorias_count': categoria.subcategorias.count(),
        }
        categorias_data.append(categoria_dict)
    
    return JsonResponse({
        'success': True,
        'data': categorias_data,
        'total': len(categorias_data)
    })


@login_required
@require_http_methods(["POST"])
def categoria_create(request):
    """Crea una nueva categoría"""
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
        if Categoria.objects.filter(nombre=nombre).exists():
            return JsonResponse({
                'success': False,
                'error': 'Ya existe una categoría con este nombre'
            }, status=400)
        
        # Obtener categoría padre si se proporciona
        categoria_padre_id = data.get('categoria_padre_id')
        categoria_padre = None
        if categoria_padre_id:
            categoria_padre = get_object_or_404(Categoria, id=categoria_padre_id)
        
        # Crear la categoría
        categoria = Categoria(
            nombre=nombre,
            descripcion=data.get('descripcion', '').strip() or None,
            categoria_padre=categoria_padre
        )
        
        # Validar antes de guardar
        categoria.full_clean()
        categoria.save()
        
        # Retornar los datos de la categoría creada
        categoria_dict = {
            'id': categoria.id,
            'nombre': categoria.nombre,
            'slug': categoria.slug,
            'descripcion': categoria.descripcion or '',
            'categoria_padre_id': categoria.categoria_padre.id if categoria.categoria_padre else None,
            'categoria_padre_nombre': categoria.categoria_padre.nombre if categoria.categoria_padre else None,
            'nivel': categoria.nivel,
            'ruta_completa': categoria.ruta_completa or categoria.nombre,
            'subcategorias_count': 0,
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Categoría creada exitosamente',
            'data': categoria_dict
        }, status=201)
        
    except ValidationError as e:
        error_msg = str(e)
        if hasattr(e, 'message_dict'):
            error_msg = ', '.join([f"{k}: {v[0]}" for k, v in e.message_dict.items()])
        return JsonResponse({
            'success': False,
            'error': error_msg
        }, status=400)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Formato JSON inválido'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al crear la categoría: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def categoria_detail(request, categoria_id):
    """Obtiene los detalles de una categoría"""
    try:
        categoria = get_object_or_404(Categoria, id=categoria_id)
        
        categoria_dict = {
            'id': categoria.id,
            'nombre': categoria.nombre,
            'slug': categoria.slug,
            'descripcion': categoria.descripcion or '',
            'categoria_padre_id': categoria.categoria_padre.id if categoria.categoria_padre else None,
            'categoria_padre_nombre': categoria.categoria_padre.nombre if categoria.categoria_padre else None,
            'nivel': categoria.nivel,
            'ruta_completa': categoria.ruta_completa or categoria.nombre,
            'subcategorias_count': categoria.subcategorias.count(),
        }
        
        return JsonResponse({
            'success': True,
            'data': categoria_dict
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener la categoría: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "PUT", "PATCH"])
def categoria_update(request, categoria_id):
    """Actualiza una categoría existente"""
    try:
        categoria = get_object_or_404(Categoria, id=categoria_id)
        
        # Manejar POST con _method para compatibilidad
        data = json.loads(request.body)
        if request.method == 'POST' and data.get('_method') == 'PUT':
            # Simular PUT desde POST
            pass
        elif request.method != 'PUT' and request.method != 'PATCH':
            return JsonResponse({
                'success': False,
                'error': 'Método no permitido'
            }, status=405)
        
        # Validar campos
        nombre = data.get('nombre', '').strip()
        if not nombre:
            return JsonResponse({
                'success': False,
                'error': 'El nombre es obligatorio'
            }, status=400)
        
        # Validar que el nombre no exista en otra categoría
        if Categoria.objects.filter(nombre=nombre).exclude(id=categoria_id).exists():
            return JsonResponse({
                'success': False,
                'error': 'Ya existe otra categoría con este nombre'
            }, status=400)
        
        # Actualizar categoría padre si se proporciona
        categoria_padre_id = data.get('categoria_padre_id')
        if categoria_padre_id == '' or categoria_padre_id is None:
            categoria.categoria_padre = None
        elif categoria_padre_id:
            # Evitar que una categoría sea padre de sí misma
            if int(categoria_padre_id) == categoria_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Una categoría no puede ser padre de sí misma'
                }, status=400)
            categoria_padre = get_object_or_404(Categoria, id=categoria_padre_id)
            categoria.categoria_padre = categoria_padre
        
        # Actualizar campos
        categoria.nombre = nombre
        categoria.descripcion = data.get('descripcion', '').strip() or None
        
        # Validar antes de guardar
        categoria.full_clean()
        categoria.save()
        
        # Retornar los datos actualizados
        categoria_dict = {
            'id': categoria.id,
            'nombre': categoria.nombre,
            'slug': categoria.slug,
            'descripcion': categoria.descripcion or '',
            'categoria_padre_id': categoria.categoria_padre.id if categoria.categoria_padre else None,
            'categoria_padre_nombre': categoria.categoria_padre.nombre if categoria.categoria_padre else None,
            'nivel': categoria.nivel,
            'ruta_completa': categoria.ruta_completa or categoria.nombre,
            'subcategorias_count': categoria.subcategorias.count(),
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Categoría actualizada exitosamente',
            'data': categoria_dict
        })
        
    except ValidationError as e:
        error_msg = str(e)
        if hasattr(e, 'message_dict'):
            error_msg = ', '.join([f"{k}: {v[0]}" for k, v in e.message_dict.items()])
        return JsonResponse({
            'success': False,
            'error': error_msg
        }, status=400)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Formato JSON inválido'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al actualizar la categoría: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "DELETE"])
def categoria_delete(request, categoria_id):
    """Elimina una categoría"""
    try:
        categoria = get_object_or_404(Categoria, id=categoria_id)
        
        # Manejar POST con _method para compatibilidad
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                if data.get('_method') != 'DELETE':
                    return JsonResponse({
                        'success': False,
                        'error': 'Método no permitido'
                    }, status=405)
            except:
                pass
        
        # Verificar si tiene subcategorías
        if categoria.subcategorias.exists():
            return JsonResponse({
                'success': False,
                'error': 'No se puede eliminar la categoría porque tiene subcategorías asociadas'
            }, status=400)
        
        nombre_categoria = categoria.nombre
        categoria.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Categoría "{nombre_categoria}" eliminada exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al eliminar la categoría: {str(e)}'
        }, status=500)


# ============================================================================
# VISTAS PARA ETIQUETAS
# ============================================================================

@login_required
@require_http_methods(["GET"])
def etiquetas_list(request):
    """Lista todas las etiquetas en formato JSON"""
    etiquetas = Etiqueta.objects.all()
    etiquetas_data = []
    
    for etiqueta in etiquetas:
        etiqueta_dict = {
            'id': etiqueta.id,
            'nombre': etiqueta.nombre,
            'slug': etiqueta.slug,
            'descripcion': etiqueta.descripcion or '',
            'color': etiqueta.color or '',
        }
        etiquetas_data.append(etiqueta_dict)
    
    return JsonResponse({
        'success': True,
        'data': etiquetas_data,
        'total': len(etiquetas_data)
    })


@login_required
@require_http_methods(["POST"])
def etiqueta_create(request):
    """Crea una nueva etiqueta"""
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
        if Etiqueta.objects.filter(nombre=nombre).exists():
            return JsonResponse({
                'success': False,
                'error': 'Ya existe una etiqueta con este nombre'
            }, status=400)
        
        # Validar formato de color si se proporciona
        color = data.get('color', '').strip()
        if color and not color.startswith('#'):
            color = '#' + color
        
        # Crear la etiqueta
        etiqueta = Etiqueta(
            nombre=nombre,
            descripcion=data.get('descripcion', '').strip() or None,
            color=color or None
        )
        
        etiqueta.full_clean()
        etiqueta.save()
        
        # Retornar los datos de la etiqueta creada
        etiqueta_dict = {
            'id': etiqueta.id,
            'nombre': etiqueta.nombre,
            'slug': etiqueta.slug,
            'descripcion': etiqueta.descripcion or '',
            'color': etiqueta.color or '',
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Etiqueta creada exitosamente',
            'data': etiqueta_dict
        }, status=201)
        
    except ValidationError as e:
        error_msg = str(e)
        if hasattr(e, 'message_dict'):
            error_msg = ', '.join([f"{k}: {v[0]}" for k, v in e.message_dict.items()])
        return JsonResponse({
            'success': False,
            'error': error_msg
        }, status=400)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Formato JSON inválido'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al crear la etiqueta: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def etiqueta_detail(request, etiqueta_id):
    """Obtiene los detalles de una etiqueta"""
    try:
        etiqueta = get_object_or_404(Etiqueta, id=etiqueta_id)
        
        etiqueta_dict = {
            'id': etiqueta.id,
            'nombre': etiqueta.nombre,
            'slug': etiqueta.slug,
            'descripcion': etiqueta.descripcion or '',
            'color': etiqueta.color or '',
        }
        
        return JsonResponse({
            'success': True,
            'data': etiqueta_dict
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener la etiqueta: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "PUT", "PATCH"])
def etiqueta_update(request, etiqueta_id):
    """Actualiza una etiqueta existente"""
    try:
        etiqueta = get_object_or_404(Etiqueta, id=etiqueta_id)
        
        # Manejar POST con _method para compatibilidad
        data = json.loads(request.body)
        if request.method == 'POST' and data.get('_method') == 'PUT':
            # Simular PUT desde POST
            pass
        elif request.method != 'PUT' and request.method != 'PATCH':
            return JsonResponse({
                'success': False,
                'error': 'Método no permitido'
            }, status=405)
        
        # Validar campos
        nombre = data.get('nombre', '').strip()
        if not nombre:
            return JsonResponse({
                'success': False,
                'error': 'El nombre es obligatorio'
            }, status=400)
        
        # Validar que el nombre no exista en otra etiqueta
        if Etiqueta.objects.filter(nombre=nombre).exclude(id=etiqueta_id).exists():
            return JsonResponse({
                'success': False,
                'error': 'Ya existe otra etiqueta con este nombre'
            }, status=400)
        
        # Validar formato de color si se proporciona
        color = data.get('color', '').strip()
        if color and not color.startswith('#'):
            color = '#' + color
        
        # Actualizar campos
        etiqueta.nombre = nombre
        etiqueta.descripcion = data.get('descripcion', '').strip() or None
        etiqueta.color = color or None
        
        etiqueta.full_clean()
        etiqueta.save()
        
        # Retornar los datos actualizados
        etiqueta_dict = {
            'id': etiqueta.id,
            'nombre': etiqueta.nombre,
            'slug': etiqueta.slug,
            'descripcion': etiqueta.descripcion or '',
            'color': etiqueta.color or '',
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Etiqueta actualizada exitosamente',
            'data': etiqueta_dict
        })
        
    except ValidationError as e:
        error_msg = str(e)
        if hasattr(e, 'message_dict'):
            error_msg = ', '.join([f"{k}: {v[0]}" for k, v in e.message_dict.items()])
        return JsonResponse({
            'success': False,
            'error': error_msg
        }, status=400)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Formato JSON inválido'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al actualizar la etiqueta: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST", "DELETE"])
def etiqueta_delete(request, etiqueta_id):
    """Elimina una etiqueta"""
    try:
        etiqueta = get_object_or_404(Etiqueta, id=etiqueta_id)
        
        # Manejar POST con _method para compatibilidad
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                if data.get('_method') != 'DELETE':
                    return JsonResponse({
                        'success': False,
                        'error': 'Método no permitido'
                    }, status=405)
            except:
                pass
        nombre_etiqueta = etiqueta.nombre
        etiqueta.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Etiqueta "{nombre_etiqueta}" eliminada exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al eliminar la etiqueta: {str(e)}'
        }, status=500)
