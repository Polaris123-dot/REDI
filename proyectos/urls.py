from django.urls import path
from . import views

app_name = 'proyectos'

urlpatterns = [
    # Página principal de proyectos
    path('', views.index, name='index'),
    
    # URLs para Tipos de Proyecto
    # Rutas específicas primero (sin parámetros dinámicos)
    path('tipos-proyecto/select/', views.tipos_proyecto_for_select, name='tipos_proyecto_for_select'),
    path('tipos-proyecto/crear/', views.tipo_proyecto_create, name='tipo_proyecto_create'),
    path('tipos-proyecto/<int:tipo_proyecto_id>/', views.tipo_proyecto_detail, name='tipo_proyecto_detail'),
    path('tipos-proyecto/<int:tipo_proyecto_id>/editar/', views.tipo_proyecto_update, name='tipo_proyecto_update'),
    path('tipos-proyecto/<int:tipo_proyecto_id>/eliminar/', views.tipo_proyecto_delete, name='tipo_proyecto_delete'),
    path('tipos-proyecto/', views.tipos_proyecto_list, name='tipos_proyecto_list'),
    
    # URLs para Campos de Tipo de Proyecto
    path('campos-tipo-proyecto/', views.campos_tipo_proyecto_list, name='campos_tipo_proyecto_list'),
    path('campos-tipo-proyecto/crear/', views.campo_tipo_proyecto_create, name='campo_tipo_proyecto_create'),
    path('campos-tipo-proyecto/<int:campo_id>/', views.campo_tipo_proyecto_detail, name='campo_tipo_proyecto_detail'),
    path('campos-tipo-proyecto/<int:campo_id>/editar/', views.campo_tipo_proyecto_update, name='campo_tipo_proyecto_update'),
    path('campos-tipo-proyecto/<int:campo_id>/eliminar/', views.campo_tipo_proyecto_delete, name='campo_tipo_proyecto_delete'),
    
    # URLs para Proyectos
    path('lista/', views.proyectos_list, name='proyectos_list'),
    path('por-tipo/<int:tipo_proyecto_id>/', views.proyectos_por_tipo, name='proyectos_por_tipo'),
    path('campos-por-tipo/<int:tipo_proyecto_id>/', views.campos_por_tipo_proyecto, name='campos_por_tipo_proyecto'),
    path('crear/', views.proyecto_create, name='proyecto_create'),
    path('<int:proyecto_id>/', views.proyecto_detail, name='proyecto_detail'),
    path('<int:proyecto_id>/editar/', views.proyecto_update, name='proyecto_update'),
    path('<int:proyecto_id>/eliminar/', views.proyecto_delete, name='proyecto_delete'),
    
    # URLs auxiliares para selects
    path('usuarios/para-select/', views.usuarios_for_select, name='usuarios_for_select'),
    
    # Wizard de acceso rápido
    path('wizard-rapido/', views.wizard_rapido, name='wizard_rapido'),
]

