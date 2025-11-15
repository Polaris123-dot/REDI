from django.urls import path
from . import views

app_name = 'busqueda'

urlpatterns = [
    # Página principal de búsqueda
    path('', views.index, name='index'),
    
    # URLs para Índices de Búsqueda
    path('indices/', views.indices_list, name='indices_list'),
    path('indices/crear/', views.indice_create, name='indice_create'),
    path('indices/<int:indice_id>/', views.indice_detail, name='indice_detail'),
    path('indices/<int:indice_id>/editar/', views.indice_update, name='indice_update'),
    path('indices/<int:indice_id>/eliminar/', views.indice_delete, name='indice_delete'),
    
    # URLs para Búsquedas
    path('busquedas/', views.busquedas_list, name='busquedas_list'),
    path('busquedas/crear/', views.busqueda_create, name='busqueda_create'),
    path('busquedas/<int:busqueda_id>/', views.busqueda_detail, name='busqueda_detail'),
    path('busquedas/<int:busqueda_id>/editar/', views.busqueda_update, name='busqueda_update'),
    path('busquedas/<int:busqueda_id>/eliminar/', views.busqueda_delete, name='busqueda_delete'),
    
    # URLs auxiliares para selects
    path('documentos/para-select/', views.documentos_for_select, name='documentos_for_select'),
    path('usuarios/para-select/', views.usuarios_for_select, name='usuarios_for_select'),
]



