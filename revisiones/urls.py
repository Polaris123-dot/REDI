from django.urls import path
from . import views

app_name = 'revisiones'

urlpatterns = [
    # Página principal de revisiones
    path('', views.index, name='index'),
    
    # URLs para Criterios de Revisión
    path('criterios/', views.criterios_list, name='criterios_list'),
    path('criterios/crear/', views.criterio_create, name='criterio_create'),
    path('criterios/<int:criterio_id>/', views.criterio_detail, name='criterio_detail'),
    path('criterios/<int:criterio_id>/editar/', views.criterio_update, name='criterio_update'),
    path('criterios/<int:criterio_id>/eliminar/', views.criterio_delete, name='criterio_delete'),
    
    # URLs para Procesos de Revisión
    path('procesos/', views.procesos_list, name='procesos_list'),
    path('procesos/crear/', views.proceso_create, name='proceso_create'),
    path('procesos/<int:proceso_id>/', views.proceso_detail, name='proceso_detail'),
    path('procesos/<int:proceso_id>/editar/', views.proceso_update, name='proceso_update'),
    path('procesos/<int:proceso_id>/eliminar/', views.proceso_delete, name='proceso_delete'),
    
    # URLs para Revisiones
    path('revisiones/', views.revisiones_list, name='revisiones_list'),
    path('revisiones/crear/', views.revision_create, name='revision_create'),
    path('revisiones/<int:revision_id>/', views.revision_detail, name='revision_detail'),
    path('revisiones/<int:revision_id>/editar/', views.revision_update, name='revision_update'),
    path('revisiones/<int:revision_id>/eliminar/', views.revision_delete, name='revision_delete'),
    
    # URLs para Evaluaciones de Criterios
    path('evaluaciones/', views.evaluaciones_list, name='evaluaciones_list'),
    path('evaluaciones/crear/', views.evaluacion_create, name='evaluacion_create'),
    path('evaluaciones/<int:evaluacion_id>/', views.evaluacion_detail, name='evaluacion_detail'),
    path('evaluaciones/<int:evaluacion_id>/editar/', views.evaluacion_update, name='evaluacion_update'),
    path('evaluaciones/<int:evaluacion_id>/eliminar/', views.evaluacion_delete, name='evaluacion_delete'),
    
    # URLs auxiliares para selects
    path('criterios/para-select/', views.criterios_for_select, name='criterios_for_select'),
    path('documentos/para-select/', views.documentos_for_select, name='documentos_for_select'),
    path('usuarios/para-select/', views.usuarios_for_select, name='usuarios_for_select'),
    path('procesos/para-select/', views.procesos_for_select, name='procesos_for_select'),
    path('revisiones/para-select/', views.revisiones_for_select, name='revisiones_for_select'),
]


