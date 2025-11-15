from django.urls import path
from . import views

app_name = 'publicaciones'

urlpatterns = [
    path('', views.index, name='index'),
    
    # URLs para Publicaciones
    path('lista/', views.publicaciones_list, name='publicaciones_list'),
    path('crear/', views.publicacion_create, name='publicacion_create'),
    path('<int:publicacion_id>/', views.publicacion_detail, name='publicacion_detail'),
    path('<int:publicacion_id>/editar/', views.publicacion_update, name='publicacion_update'),
    path('<int:publicacion_id>/eliminar/', views.publicacion_delete, name='publicacion_delete'),
    path('generar-slug-preview/', views.generar_slug_preview, name='generar_slug_preview'),
    
    # URLs auxiliares para selects
    path('proyectos/para-select/', views.proyectos_for_select, name='proyectos_for_select'),
    path('categorias/para-select/', views.categorias_for_select, name='categorias_for_select'),
    path('etiquetas/para-select/', views.etiquetas_for_select, name='etiquetas_for_select'),
    path('usuarios/para-select/', views.usuarios_for_select, name='usuarios_for_select'),
]
