from django.urls import path
from . import views

app_name = 'interaccion'

urlpatterns = [
    # Página principal de interacción
    path('', views.index, name='index'),
    
    # URLs para Comentarios
    path('comentarios/', views.comentarios_list, name='comentarios_list'),
    path('comentarios/crear/', views.comentario_create, name='comentario_create'),
    path('comentarios/<int:comentario_id>/', views.comentario_detail, name='comentario_detail'),
    path('comentarios/<int:comentario_id>/editar/', views.comentario_update, name='comentario_update'),
    path('comentarios/<int:comentario_id>/eliminar/', views.comentario_delete, name='comentario_delete'),
    
    # URLs para Valoraciones
    path('valoraciones/', views.valoraciones_list, name='valoraciones_list'),
    path('valoraciones/crear/', views.valoracion_create, name='valoracion_create'),
    path('valoraciones/<int:valoracion_id>/', views.valoracion_detail, name='valoracion_detail'),
    path('valoraciones/<int:valoracion_id>/editar/', views.valoracion_update, name='valoracion_update'),
    path('valoraciones/<int:valoracion_id>/eliminar/', views.valoracion_delete, name='valoracion_delete'),
    
    # URLs para Citas
    path('citas/', views.citas_list, name='citas_list'),
    path('citas/crear/', views.cita_create, name='cita_create'),
    path('citas/<int:cita_id>/', views.cita_detail, name='cita_detail'),
    path('citas/<int:cita_id>/editar/', views.cita_update, name='cita_update'),
    path('citas/<int:cita_id>/eliminar/', views.cita_delete, name='cita_delete'),
    
    # URLs para Referencias Bibliográficas
    path('referencias/', views.referencias_list, name='referencias_list'),
    path('referencias/crear/', views.referencia_create, name='referencia_create'),
    path('referencias/<int:referencia_id>/', views.referencia_detail, name='referencia_detail'),
    path('referencias/<int:referencia_id>/editar/', views.referencia_update, name='referencia_update'),
    path('referencias/<int:referencia_id>/eliminar/', views.referencia_delete, name='referencia_delete'),
    
    # URLs auxiliares para selects
    path('documentos/para-select/', views.documentos_for_select, name='documentos_for_select'),
    path('usuarios/para-select/', views.usuarios_for_select, name='usuarios_for_select'),
]
