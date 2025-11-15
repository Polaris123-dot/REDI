from django.urls import path
from . import views

app_name = 'notificaciones'

urlpatterns = [
    # Página principal de notificaciones
    path('', views.index, name='index'),
    
    # URLs para Tipos de Notificación
    path('tipos/', views.tipos_list, name='tipos_list'),
    path('tipos/crear/', views.tipo_create, name='tipo_create'),
    path('tipos/<int:tipo_id>/', views.tipo_detail, name='tipo_detail'),
    path('tipos/<int:tipo_id>/editar/', views.tipo_update, name='tipo_update'),
    path('tipos/<int:tipo_id>/eliminar/', views.tipo_delete, name='tipo_delete'),
    
    # URLs para Notificaciones
    path('notificaciones/', views.notificaciones_list, name='notificaciones_list'),
    path('notificaciones/crear/', views.notificacion_create, name='notificacion_create'),
    path('notificaciones/<int:notificacion_id>/', views.notificacion_detail, name='notificacion_detail'),
    path('notificaciones/<int:notificacion_id>/editar/', views.notificacion_update, name='notificacion_update'),
    path('notificaciones/<int:notificacion_id>/eliminar/', views.notificacion_delete, name='notificacion_delete'),
    path('notificaciones/<int:notificacion_id>/marcar-leida/', views.notificacion_marcar_leida, name='notificacion_marcar_leida'),
    path('notificaciones/<int:notificacion_id>/marcar-no-leida/', views.notificacion_marcar_no_leida, name='notificacion_marcar_no_leida'),
    
    # URLs auxiliares para selects
    path('usuarios/para-select/', views.usuarios_for_select, name='usuarios_for_select'),
    path('documentos/para-select/', views.documentos_for_select, name='documentos_for_select'),
    path('tipos/para-select/', views.tipos_for_select, name='tipos_for_select'),
]



