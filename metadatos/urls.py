from django.urls import path
from . import views

app_name = 'metadatos'

urlpatterns = [
    # Página principal de metadatos
    path('', views.index, name='index'),
    
    # URLs para Esquemas de Metadatos
    path('esquemas/', views.esquemas_list, name='esquemas_list'),
    path('esquemas/crear/', views.esquema_create, name='esquema_create'),
    path('esquemas/<int:esquema_id>/', views.esquema_detail, name='esquema_detail'),
    path('esquemas/<int:esquema_id>/editar/', views.esquema_update, name='esquema_update'),
    path('esquemas/<int:esquema_id>/eliminar/', views.esquema_delete, name='esquema_delete'),
    
    # URLs para Campos de Metadatos
    path('campos/', views.campos_list, name='campos_list'),
    path('campos/crear/', views.campo_create, name='campo_create'),
    path('campos/<int:campo_id>/', views.campo_detail, name='campo_detail'),
    path('campos/<int:campo_id>/editar/', views.campo_update, name='campo_update'),
    path('campos/<int:campo_id>/eliminar/', views.campo_delete, name='campo_delete'),
    
    # URLs para Metadatos de Documentos
    path('metadatos-documentos/', views.metadatos_documentos_list, name='metadatos_documentos_list'),
    path('metadatos-documentos/crear/', views.metadato_documento_create, name='metadato_documento_create'),
    path('metadatos-documentos/<int:metadato_id>/', views.metadato_documento_detail, name='metadato_documento_detail'),
    path('metadatos-documentos/<int:metadato_id>/editar/', views.metadato_documento_update, name='metadato_documento_update'),
    path('metadatos-documentos/<int:metadato_id>/eliminar/', views.metadato_documento_delete, name='metadato_documento_delete'),
    
    # URLs auxiliares para selects
    path('esquemas/para-select/', views.esquemas_for_select, name='esquemas_for_select'),
    path('campos/para-select/', views.campos_for_select, name='campos_for_select'),
    path('documentos/para-select/', views.documentos_for_select, name='documentos_for_select'),
]



