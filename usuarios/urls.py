from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    # URLs de autenticación
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Panel principal (accesible para todos los usuarios autenticados)
    path('panel/', views.panel, name='panel'),
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    path('perfil/', views.perfil_view, name='perfil'),
=======
    path('perfil/', views.perfil_usuario, name='perfil'),
>>>>>>> Stashed changes
=======
    path('perfil/', views.perfil_usuario, name='perfil'),
>>>>>>> Stashed changes
    
    # URLs de usuarios
    path('usuarios/', views.lista_usuarios, name='lista_usuarios'),
    path('crear/', views.crear_usuario, name='crear_usuario'),
    path('<int:user_id>/', views.detalle_usuario, name='detalle_usuario'),
    path('<int:user_id>/editar/', views.editar_usuario, name='editar_usuario'),
    path('<int:user_id>/eliminar/', views.eliminar_usuario, name='eliminar_usuario'),
    
    # URLs de grupos (roles)
    path('grupos/', views.lista_grupos, name='lista_grupos'),
    path('grupos/crear/', views.crear_grupo, name='crear_grupo'),
    path('grupos/<int:grupo_id>/', views.detalle_grupo, name='detalle_grupo'),
    path('grupos/<int:grupo_id>/permisos/', views.gestionar_permisos_grupo, name='gestionar_permisos_grupo'),
    path('grupos/<int:grupo_id>/eliminar/', views.eliminar_grupo, name='eliminar_grupo'),
]

