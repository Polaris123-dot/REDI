from django.urls import path
from . import views

app_name = 'estadisticas'

urlpatterns = [
    # Página principal de estadísticas
    path('', views.index, name='index'),
    
    # URLs para Visitas de Documentos
    path('visitas/', views.visitas_list, name='visitas_list'),
    path('visitas/crear/', views.visita_create, name='visita_create'),
    path('visitas/<int:visita_id>/', views.visita_detail, name='visita_detail'),
    path('visitas/<int:visita_id>/editar/', views.visita_update, name='visita_update'),
    path('visitas/<int:visita_id>/eliminar/', views.visita_delete, name='visita_delete'),
    
    # URLs para Descargas de Archivos
    path('descargas/', views.descargas_list, name='descargas_list'),
    path('descargas/crear/', views.descarga_create, name='descarga_create'),
    path('descargas/<int:descarga_id>/', views.descarga_detail, name='descarga_detail'),
    path('descargas/<int:descarga_id>/editar/', views.descarga_update, name='descarga_update'),
    path('descargas/<int:descarga_id>/eliminar/', views.descarga_delete, name='descarga_delete'),
    
    # URLs para Estadísticas Agregadas
    path('agregadas/', views.estadisticas_agregadas_list, name='estadisticas_agregadas_list'),
    path('agregadas/crear/', views.estadistica_agregada_create, name='estadistica_agregada_create'),
    path('agregadas/<int:estadistica_id>/', views.estadistica_agregada_detail, name='estadistica_agregada_detail'),
    path('agregadas/<int:estadistica_id>/editar/', views.estadistica_agregada_update, name='estadistica_agregada_update'),
    path('agregadas/<int:estadistica_id>/eliminar/', views.estadistica_agregada_delete, name='estadistica_agregada_delete'),
    
    # URLs auxiliares para selects
    path('documentos/para-select/', views.documentos_for_select, name='documentos_for_select'),
    path('archivos/para-select/', views.archivos_for_select, name='archivos_for_select'),
    path('usuarios/para-select/', views.usuarios_for_select, name='usuarios_for_select'),
]



