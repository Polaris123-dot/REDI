from django.urls import path
from . import views

app_name = 'repositorio'

urlpatterns = [
    # Página principal de repositorio (redirige a configuración)
    path('', views.index, name='index'),
    # Páginas separadas por sección
    path('configuracion/', views.configuracion, name='configuracion'),
    path('organizacion/', views.organizacion, name='organizacion'),
    path('personal/', views.personal, name='personal'),
    
    # URLs para Tipos de Recurso
    path('tipos-recurso/', views.tipos_recurso_list, name='tipos_recurso_list'),
    path('tipos-recurso/crear/', views.tipo_recurso_create, name='tipo_recurso_create'),
    path('tipos-recurso/<int:tipo_recurso_id>/', views.tipo_recurso_detail, name='tipo_recurso_detail'),
    path('tipos-recurso/<int:tipo_recurso_id>/editar/', views.tipo_recurso_update, name='tipo_recurso_update'),
    path('tipos-recurso/<int:tipo_recurso_id>/eliminar/', views.tipo_recurso_delete, name='tipo_recurso_delete'),
    
    # URLs para Estados de Documento
    path('estados-documento/', views.estados_documento_list, name='estados_documento_list'),
    path('estados-documento/crear/', views.estado_documento_create, name='estado_documento_create'),
    path('estados-documento/<int:estado_documento_id>/', views.estado_documento_detail, name='estado_documento_detail'),
    path('estados-documento/<int:estado_documento_id>/editar/', views.estado_documento_update, name='estado_documento_update'),
    path('estados-documento/<int:estado_documento_id>/eliminar/', views.estado_documento_delete, name='estado_documento_delete'),
    
    # URLs para Comunidades
    path('comunidades/', views.comunidades_list, name='comunidades_list'),
    path('comunidades/para-select/', views.comunidades_for_select, name='comunidades_for_select'),
    path('comunidades/crear/', views.comunidad_create, name='comunidad_create'),
    path('comunidades/<int:comunidad_id>/', views.comunidad_detail, name='comunidad_detail'),
    path('comunidades/<int:comunidad_id>/editar/', views.comunidad_update, name='comunidad_update'),
    path('comunidades/<int:comunidad_id>/eliminar/', views.comunidad_delete, name='comunidad_delete'),
    
    # URLs para Colecciones
    path('colecciones/', views.colecciones_list, name='colecciones_list'),
    path('colecciones/para-select/', views.colecciones_for_select, name='colecciones_for_select'),
    path('colecciones/por-comunidad/<int:comunidad_id>/', views.colecciones_por_comunidad, name='colecciones_por_comunidad'),
    path('colecciones/crear/', views.coleccion_create, name='coleccion_create'),
    path('colecciones/<int:coleccion_id>/', views.coleccion_detail, name='coleccion_detail'),
    path('colecciones/<int:coleccion_id>/editar/', views.coleccion_update, name='coleccion_update'),
    path('colecciones/<int:coleccion_id>/eliminar/', views.coleccion_delete, name='coleccion_delete'),
    
    # URLs para Licencias
    path('licencias/', views.licencias_list, name='licencias_list'),
    path('licencias/crear/', views.licencia_create, name='licencia_create'),
    path('licencias/<int:licencia_id>/', views.licencia_detail, name='licencia_detail'),
    path('licencias/<int:licencia_id>/editar/', views.licencia_update, name='licencia_update'),
    path('licencias/<int:licencia_id>/eliminar/', views.licencia_delete, name='licencia_delete'),
    
    # URLs para Documentos
    path('documentos/', views.documentos_list, name='documentos_list'),
    path('documentos/disponibles/', views.documentos_disponibles, name='documentos_disponibles'),
    path('documentos/crear/', views.documento_create, name='documento_create'),
    path('documentos/<int:documento_id>/', views.documento_detail, name='documento_detail'),
    path('documentos/<int:documento_id>/editar/', views.documento_update, name='documento_update'),
    path('documentos/<int:documento_id>/eliminar/', views.documento_delete, name='documento_delete'),
    
    # URLs para Autores
    path('autores/', views.autores_list, name='autores_list'),
    path('autores/por-documento/<int:documento_id>/', views.autores_por_documento, name='autores_por_documento'),
    path('autores/crear/', views.autor_create, name='autor_create'),
    path('autores/<int:autor_id>/', views.autor_detail, name='autor_detail'),
    path('autores/<int:autor_id>/editar/', views.autor_update, name='autor_update'),
    path('autores/<int:autor_id>/eliminar/', views.autor_delete, name='autor_delete'),
    
    # URLs para Colaboradores
    path('colaboradores/', views.colaboradores_list, name='colaboradores_list'),
    path('colaboradores/por-documento/<int:documento_id>/', views.colaboradores_por_documento, name='colaboradores_por_documento'),
    path('colaboradores/crear/', views.colaborador_create, name='colaborador_create'),
    path('colaboradores/<int:colaborador_id>/', views.colaborador_detail, name='colaborador_detail'),
    path('colaboradores/<int:colaborador_id>/editar/', views.colaborador_update, name='colaborador_update'),
    path('colaboradores/<int:colaborador_id>/eliminar/', views.colaborador_delete, name='colaborador_delete'),
    
    # URLs para Versiones de Documento
    path('versiones/', views.versiones_list, name='versiones_list'),
    path('versiones/por-documento/<int:documento_id>/', views.versiones_por_documento, name='versiones_por_documento'),
    path('versiones/crear/', views.version_create, name='version_create'),
    path('versiones/<int:version_id>/', views.version_detail, name='version_detail'),
    path('versiones/<int:version_id>/editar/', views.version_update, name='version_update'),
    path('versiones/<int:version_id>/eliminar/', views.version_delete, name='version_delete'),
    
    # URLs para Archivos (PDFs)
    path('archivos/', views.archivos_list, name='archivos_list'),
    path('archivos/por-documento/<int:documento_id>/', views.archivos_por_documento, name='archivos_por_documento'),
    path('archivos/por-version/<int:version_id>/', views.archivos_por_version, name='archivos_por_version'),
    path('archivos/crear/', views.archivo_create, name='archivo_create'),
    path('archivos/<int:archivo_id>/', views.archivo_detail, name='archivo_detail'),
    path('archivos/<int:archivo_id>/editar/', views.archivo_update, name='archivo_update'),
    path('archivos/<int:archivo_id>/eliminar/', views.archivo_delete, name='archivo_delete'),
    path('archivos/<int:archivo_id>/descargar/', views.archivo_download, name='archivo_download'),
    
    # URLs auxiliares para selects
    path('usuarios/para-select/', views.usuarios_for_select, name='usuarios_for_select'),
    path('categorias/para-select/', views.categorias_for_select, name='categorias_for_select'),
    path('etiquetas/para-select/', views.etiquetas_for_select, name='etiquetas_for_select'),
    path('tipos-recurso/para-select/', views.tipos_recurso_for_select, name='tipos_recurso_for_select'),
    path('estados-documento/para-select/', views.estados_documento_for_select, name='estados_documento_for_select'),
    path('licencias/para-select/', views.licencias_for_select, name='licencias_for_select'),
]
