from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test, login_required, permission_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User, Group, Permission
from .models import Persona
from .forms import UserUpdateForm, PersonaUpdateForm
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from django.core.exceptions import PermissionDenied


def is_superuser(user):
    """Verifica si el usuario es superusuario"""
    return user.is_authenticated and user.is_superuser


@require_http_methods(["GET", "POST"])
def login_view(request):
    """Vista de login"""
    if request.user.is_authenticated:
        # Redirigir al panel si ya está autenticado
        next_url = request.GET.get('next', None)
        if next_url:
            return redirect(next_url)
        return redirect('usuarios:panel')
    
    next_url = request.GET.get('next', None)
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        next_param = request.POST.get('next', next_url)
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    if next_param and next_param != 'None':
                        return redirect(next_param)
                    return redirect('usuarios:panel')
                else:
                    messages.error(request, 'Tu cuenta está desactivada.')
            else:
                messages.error(request, 'Usuario o contraseña incorrectos.')
        else:
            messages.error(request, 'Por favor, completa todos los campos.')
    
    context = {
        'next_url': next_url,
    }
    return render(request, 'usuarios/login.html', context)


@login_required
def logout_view(request):
    """Vista de logout"""
    from django.contrib.auth import logout
    logout(request)
    messages.success(request, 'Has cerrado sesión exitosamente.')
    return redirect('usuarios:login')


@login_required
def panel(request):
    """Panel principal accesible para todos los usuarios autenticados"""
    # Obtener el nombre completo o username
    nombre_usuario = request.user.get_full_name() if request.user.get_full_name() else request.user.username
    
    # Verificar permisos para cada módulo
    # Catalogación
    can_view_catalogacion = (request.user.has_perm('catalogacion.view_categoria') or 
                            request.user.has_perm('catalogacion.view_etiqueta') or 
                            request.user.is_superuser)
    can_add_catalogacion = (request.user.has_perm('catalogacion.add_categoria') or 
                           request.user.has_perm('catalogacion.add_etiqueta') or 
                           request.user.is_superuser)
    
    # Proyectos
    can_view_proyectos = (request.user.has_perm('proyectos.view_proyecto') or 
                         request.user.has_perm('proyectos.view_tipoproyecto') or 
                         request.user.is_superuser)
    can_add_proyectos = (request.user.has_perm('proyectos.add_proyecto') or 
                        request.user.has_perm('proyectos.add_tipoproyecto') or 
                        request.user.is_superuser)
    
    # Repositorio
    can_view_repositorio = (request.user.has_perm('repositorio.view_tiporecurso') or 
                           request.user.has_perm('repositorio.view_estadodocumento') or
                           request.user.has_perm('repositorio.view_comunidad') or
                           request.user.has_perm('repositorio.view_coleccion') or
                           request.user.has_perm('repositorio.view_licencia') or
                           request.user.is_superuser)
    can_add_repositorio = (request.user.has_perm('repositorio.add_tiporecurso') or 
                          request.user.has_perm('repositorio.add_estadodocumento') or
                          request.user.has_perm('repositorio.add_comunidad') or
                          request.user.has_perm('repositorio.add_coleccion') or
                          request.user.has_perm('repositorio.add_licencia') or
                          request.user.is_superuser)
    
    # Publicaciones
    can_view_publicaciones = (request.user.has_perm('publicaciones.view_publicacion') or 
                             request.user.is_superuser)
    can_add_publicaciones = (request.user.has_perm('publicaciones.add_publicacion') or 
                            request.user.is_superuser)
    
    # Interacción
    can_view_interaccion = (request.user.has_perm('interaccion.view_comentario') or 
                           request.user.has_perm('interaccion.view_valoracion') or
                           request.user.has_perm('interaccion.view_cita') or
                           request.user.has_perm('interaccion.view_referenciabibliografica') or
                           request.user.is_superuser)
    can_add_interaccion = (request.user.has_perm('interaccion.add_comentario') or 
                          request.user.has_perm('interaccion.add_valoracion') or
                          request.user.has_perm('interaccion.add_cita') or
                          request.user.has_perm('interaccion.add_referenciabibliografica') or
                          request.user.is_superuser)
    
    # Notificaciones
    can_view_notificaciones = (request.user.has_perm('notificaciones.view_tiponotificacion') or 
                               request.user.has_perm('notificaciones.view_notificacion') or
                               request.user.is_superuser)
    can_add_notificaciones = (request.user.has_perm('notificaciones.add_tiponotificacion') or 
                              request.user.has_perm('notificaciones.add_notificacion') or
                              request.user.is_superuser)
    
    # Configuración (solo superusuarios o usuarios con permisos específicos)
    can_view_configuracion = (request.user.has_perm('configuracion.view_configuracionsistema') or 
                              request.user.has_perm('configuracion.view_logsistema') or
                              request.user.is_superuser)
    can_add_configuracion = (request.user.has_perm('configuracion.add_configuracionsistema') or
                             request.user.is_superuser)
    
    # Metadatos
    can_view_metadatos = (request.user.has_perm('metadatos.view_esquametadatos') or 
                         request.user.has_perm('metadatos.view_campometadatos') or
                         request.user.has_perm('metadatos.view_metadatosdocumento') or
                         request.user.is_superuser)
    can_add_metadatos = (request.user.has_perm('metadatos.add_esquametadatos') or 
                        request.user.has_perm('metadatos.add_campometadatos') or
                        request.user.has_perm('metadatos.add_metadatosdocumento') or
                        request.user.is_superuser)
    
    # Estadísticas
    can_view_estadisticas = (request.user.has_perm('estadisticas.view_visitadocumento') or 
                            request.user.has_perm('estadisticas.view_descargaarchivo') or
                            request.user.has_perm('estadisticas.view_estadisticaagregada') or
                            request.user.is_superuser)
    can_add_estadisticas = (request.user.has_perm('estadisticas.add_visitadocumento') or 
                           request.user.has_perm('estadisticas.add_descargaarchivo') or
                           request.user.has_perm('estadisticas.add_estadisticaagregada') or
                           request.user.is_superuser)
    
    # Búsqueda
    can_view_busqueda = (request.user.has_perm('busqueda.view_indicebusqueda') or 
                        request.user.has_perm('busqueda.view_busqueda') or
                        request.user.is_superuser)
    can_add_busqueda = (request.user.has_perm('busqueda.add_indicebusqueda') or 
                       request.user.has_perm('busqueda.add_busqueda') or
                       request.user.is_superuser)
    
    # Revisiones
    can_view_revisiones = (request.user.has_perm('revisiones.view_criteriorevision') or 
                          request.user.has_perm('revisiones.view_procesorevision') or
                          request.user.has_perm('revisiones.view_revision') or
                          request.user.has_perm('revisiones.view_evaluacioncriterio') or
                          request.user.is_superuser)
    can_add_revisiones = (request.user.has_perm('revisiones.add_criteriorevision') or 
                         request.user.has_perm('revisiones.add_procesorevision') or
                         request.user.has_perm('revisiones.add_revision') or
                         request.user.has_perm('revisiones.add_evaluacioncriterio') or
                         request.user.is_superuser)
    
    # Usuarios
    can_view_usuarios = (request.user.has_perm('auth.view_user') or 
                        request.user.is_superuser)
    can_manage_roles = request.user.is_superuser
    
    context = {
        'usuario': request.user,
        'nombre_usuario': nombre_usuario,
        'can_view_catalogacion': can_view_catalogacion,
        'can_add_catalogacion': can_add_catalogacion,
        'can_view_proyectos': can_view_proyectos,
        'can_add_proyectos': can_add_proyectos,
        'can_view_repositorio': can_view_repositorio,
        'can_add_repositorio': can_add_repositorio,
        'can_view_publicaciones': can_view_publicaciones,
        'can_add_publicaciones': can_add_publicaciones,
        'can_view_interaccion': can_view_interaccion,
        'can_add_interaccion': can_add_interaccion,
        'can_view_notificaciones': can_view_notificaciones,
        'can_add_notificaciones': can_add_notificaciones,
        'can_view_configuracion': can_view_configuracion,
        'can_add_configuracion': can_add_configuracion,
        'can_view_metadatos': can_view_metadatos,
        'can_add_metadatos': can_add_metadatos,
        'can_view_estadisticas': can_view_estadisticas,
        'can_add_estadisticas': can_add_estadisticas,
        'can_view_busqueda': can_view_busqueda,
        'can_add_busqueda': can_add_busqueda,
        'can_view_revisiones': can_view_revisiones,
        'can_add_revisiones': can_add_revisiones,
        'can_view_usuarios': can_view_usuarios,
        'can_manage_roles': can_manage_roles,
    }
    return render(request, 'usuarios/panel.html', context)


@login_required
def lista_usuarios(request):
    """Lista todos los usuarios del sistema"""
    # Verificar si el usuario tiene permiso para ver usuarios
    if not request.user.has_perm('auth.view_user') and not request.user.is_superuser:
        messages.warning(request, 'No tienes permisos para ver la lista de usuarios.')
        return redirect('usuarios:panel')
    
    query = request.GET.get('q', '')
    usuarios = User.objects.all().order_by('username')
    
    if query:
        usuarios = usuarios.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )
    
    # Paginación
    paginator = Paginator(usuarios, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estadísticas para las cards
    total_usuarios = User.objects.count()
    usuarios_activos = User.objects.filter(is_active=True).count()
    total_grupos = Group.objects.count()
    superusuarios = User.objects.filter(is_superuser=True).count()
    
    context = {
        'usuarios': page_obj,
        'query': query,
        'total_usuarios': total_usuarios,
        'usuarios_activos': usuarios_activos,
        'total_grupos': total_grupos,
        'superusuarios': superusuarios,
    }
    return render(request, 'usuarios/lista_usuarios.html', context)


@login_required
def detalle_usuario(request, user_id):
    """Muestra el detalle de un usuario y permite asignar roles"""
    # Verificar permisos para ver usuarios
    if not request.user.has_perm('auth.view_user') and not request.user.is_superuser:
        messages.warning(request, 'No tienes permisos para ver detalles de usuarios.')
        return redirect('usuarios:panel')
    usuario = get_object_or_404(User, id=user_id)
    grupos_disponibles = Group.objects.all()
    grupos_usuario = usuario.groups.all()
    
    if request.method == 'POST':
        # Verificar permiso para cambiar usuarios antes de actualizar grupos
        if not request.user.has_perm('auth.change_user') and not request.user.is_superuser:
            messages.error(request, 'No tienes permisos para modificar usuarios.')
            return redirect('usuarios:lista_usuarios')
        
        # Asignar o quitar grupos
        grupos_seleccionados = request.POST.getlist('grupos')
        usuario.groups.set(grupos_seleccionados)
        messages.success(request, f'Roles actualizados para {usuario.username}')
        return redirect('usuarios:detalle_usuario', user_id=user_id)
    
    context = {
        'usuario': usuario,
        'grupos_disponibles': grupos_disponibles,
        'grupos_usuario': grupos_usuario,
    }
    return render(request, 'usuarios/detalle_usuario.html', context)


@login_required
def crear_usuario(request):
    """Crea un nuevo usuario"""
    # Verificar permiso para crear usuarios
    if not request.user.has_perm('auth.add_user') and not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para crear usuarios.')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            from django.http import JsonResponse
            return JsonResponse({'error': 'No tienes permisos para crear usuarios.'}, status=403)
        return redirect('usuarios:lista_usuarios')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        password = request.POST.get('password')
        is_staff = request.POST.get('is_staff') == 'on'
        is_superuser = request.POST.get('is_superuser') == 'on'
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'El nombre de usuario ya existe')
        else:
            usuario = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=password,
                is_staff=is_staff,
                is_superuser=is_superuser
            )
            messages.success(request, f'Usuario {username} creado exitosamente')
            return redirect('usuarios:detalle_usuario', user_id=usuario.id)
    
    return render(request, 'usuarios/crear_usuario.html')


@login_required
def editar_usuario(request, user_id):
    """Edita un usuario existente"""
    # Verificar permiso para editar usuarios
    if not request.user.has_perm('auth.change_user') and not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para editar usuarios.')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            from django.http import JsonResponse
            return JsonResponse({'error': 'No tienes permisos para editar usuarios.'}, status=403)
        return redirect('usuarios:lista_usuarios')
    
    usuario = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        usuario.email = request.POST.get('email')
        usuario.first_name = request.POST.get('first_name', '')
        usuario.last_name = request.POST.get('last_name', '')
        usuario.is_staff = request.POST.get('is_staff') == 'on'
        usuario.is_superuser = request.POST.get('is_superuser') == 'on'
        usuario.is_active = request.POST.get('is_active') == 'on'
        
        password = request.POST.get('password')
        if password:
            usuario.set_password(password)
        
        usuario.save()
        messages.success(request, f'Usuario {usuario.username} actualizado exitosamente')
        return redirect('usuarios:detalle_usuario', user_id=user_id)
    
    context = {
        'usuario': usuario,
    }
    return render(request, 'usuarios/editar_usuario.html', context)


@login_required
def eliminar_usuario(request, user_id):
    """Elimina un usuario"""
    # Verificar permiso para eliminar usuarios
    if not request.user.has_perm('auth.delete_user') and not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para eliminar usuarios.')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            from django.http import JsonResponse
            return JsonResponse({'error': 'No tienes permisos para eliminar usuarios.'}, status=403)
        return redirect('usuarios:lista_usuarios')
    
    usuario = get_object_or_404(User, id=user_id)
    
    # No permitir que un usuario se elimine a sí mismo
    if usuario == request.user:
        messages.error(request, 'No puedes eliminar tu propia cuenta.')
        return redirect('usuarios:lista_usuarios')
    
    if request.method == 'POST':
        username = usuario.username
        usuario.delete()
        messages.success(request, f'Usuario {username} eliminado exitosamente')
        return redirect('usuarios:lista_usuarios')
    
    context = {
        'usuario': usuario,
    }
    return render(request, 'usuarios/eliminar_usuario.html', context)


@login_required
def lista_grupos(request):
    """Lista todos los grupos (roles) del sistema"""
    # Solo superusuarios pueden gestionar grupos
    if not request.user.is_superuser:
        messages.warning(request, 'No tienes permisos para gestionar roles.')
        return redirect('usuarios:panel')
    query = request.GET.get('q', '')
    grupos = Group.objects.all().order_by('name')
    
    if query:
        grupos = grupos.filter(name__icontains=query)
    
    # Contar usuarios en cada grupo
    grupos_con_usuarios = []
    for grupo in grupos:
        grupos_con_usuarios.append({
            'grupo': grupo,
            'num_usuarios': grupo.user_set.count()
        })
    
    context = {
        'grupos': grupos_con_usuarios,
        'query': query,
    }
    return render(request, 'usuarios/lista_grupos.html', context)


@login_required
def crear_grupo(request):
    """Crea un nuevo grupo (rol)"""
    # Solo superusuarios pueden crear grupos
    if not request.user.is_superuser:
        messages.warning(request, 'No tienes permisos para crear roles.')
        return redirect('usuarios:panel')
    if request.method == 'POST':
        nombre = request.POST.get('name')
        if Group.objects.filter(name=nombre).exists():
            messages.error(request, 'El grupo ya existe')
        else:
            grupo = Group.objects.create(name=nombre)
            messages.success(request, f'Grupo {nombre} creado exitosamente')
            return redirect('usuarios:detalle_grupo', grupo_id=grupo.id)
    
    return render(request, 'usuarios/crear_grupo.html')


@login_required
def detalle_grupo(request, grupo_id):
    """Muestra el detalle de un grupo y sus usuarios"""
    # Solo superusuarios pueden ver detalles de grupos
    if not request.user.is_superuser:
        messages.warning(request, 'No tienes permisos para ver esta página.')
        return redirect('usuarios:panel')
    grupo = get_object_or_404(Group, id=grupo_id)
    usuarios_grupo = grupo.user_set.all()
    todos_usuarios = User.objects.all()
    
    if request.method == 'POST':
        # Agregar usuarios al grupo
        usuarios_seleccionados = request.POST.getlist('usuarios')
        grupo.user_set.set(usuarios_seleccionados)
        messages.success(request, f'Usuarios actualizados para el grupo {grupo.name}')
        return redirect('usuarios:detalle_grupo', grupo_id=grupo_id)
    
    context = {
        'grupo': grupo,
        'usuarios_grupo': usuarios_grupo,
        'todos_usuarios': todos_usuarios,
    }
    return render(request, 'usuarios/detalle_grupo.html', context)


@login_required
def gestionar_permisos_grupo(request, grupo_id):
    """Gestiona los permisos asignados a un grupo (rol)"""
    # Solo superusuarios pueden gestionar permisos
    if not request.user.is_superuser:
        messages.warning(request, 'No tienes permisos para gestionar permisos de roles.')
        return redirect('usuarios:panel')
    
    grupo = get_object_or_404(Group, id=grupo_id)
    
    if request.method == 'POST':
        # Obtener los permisos seleccionados
        permisos_seleccionados = request.POST.getlist('permisos')
        
        # Convertir IDs a objetos Permission
        permisos_objetos = Permission.objects.filter(id__in=permisos_seleccionados)
        
        # Asignar permisos al grupo
        grupo.permissions.set(permisos_objetos)
        
        messages.success(request, f'Permisos actualizados para el rol {grupo.name}')
        return redirect('usuarios:gestionar_permisos_grupo', grupo_id=grupo_id)
    
    # Obtener todos los permisos disponibles, organizados por ContentType
    todos_permisos = Permission.objects.all().select_related('content_type').order_by(
        'content_type__app_label', 'content_type__model', 'codename'
    )
    
    # Permisos ya asignados al grupo
    permisos_grupo = grupo.permissions.all()
    permisos_grupo_ids = set(permisos_grupo.values_list('id', flat=True))
    
    # Separar permisos disponibles y asignados
    permisos_disponibles = [p for p in todos_permisos if p.id not in permisos_grupo_ids]
    permisos_asignados = list(permisos_grupo)
    
    # Organizar permisos por app y modelo para mejor visualización
    permisos_por_app = {}
    for permiso in todos_permisos:
        app_label = permiso.content_type.app_label
        model_name = permiso.content_type.model
        key = f"{app_label}_{model_name}"
        
        if key not in permisos_por_app:
            permisos_por_app[key] = {
                'app_label': app_label,
                'model_name': model_name,
                'permisos': []
            }
        permisos_por_app[key]['permisos'].append(permiso)
    
    context = {
        'grupo': grupo,
        'permisos_disponibles': permisos_disponibles,
        'permisos_asignados': permisos_asignados,
        'todos_permisos': todos_permisos,
        'permisos_por_app': permisos_por_app,
        'permisos_grupo_ids': permisos_grupo_ids,
    }
    return render(request, 'usuarios/gestionar_permisos_grupo.html', context)


@login_required
def eliminar_grupo(request, grupo_id):
    # Solo superusuarios pueden eliminar grupos
    if not request.user.is_superuser:
        messages.warning(request, 'No tienes permisos para eliminar roles.')
        return redirect('usuarios:panel')
    """Elimina un grupo"""
    grupo = get_object_or_404(Group, id=grupo_id)
    if request.method == 'POST':
        nombre = grupo.name
        grupo.delete()
        messages.success(request, f'Grupo {nombre} eliminado exitosamente')
        return redirect('usuarios:lista_grupos')
    
    context = {
        'grupo': grupo,
    }
    return render(request, 'usuarios/eliminar_grupo.html', context)


@login_required
def perfil_view(request):
    """Vista para ver y editar el perfil del usuario"""
    # Asegurar que el usuario tenga un objeto Persona asociado
    persona, created = Persona.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = PersonaUpdateForm(request.POST, request.FILES, instance=persona)
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Tu perfil ha sido actualizado exitosamente.')
            return redirect('usuarios:perfil')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = PersonaUpdateForm(instance=persona)
    
    context = {
        'u_form': u_form,
        'p_form': p_form,
        'title': 'Mi Perfil'
    }
    return render(request, 'usuarios/perfil.html', context)
