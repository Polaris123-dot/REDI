from django.urls import path
from . import views

app_name = 'configuracion'

urlpatterns = [
    # Página principal de configuración
    path('', views.index, name='index'),
    
    # URLs para Configuración del Sistema
    path('configuraciones/', views.configuraciones_list, name='configuraciones_list'),
    path('configuraciones/crear/', views.configuracion_create, name='configuracion_create'),
    path('configuraciones/<int:configuracion_id>/', views.configuracion_detail, name='configuracion_detail'),
    path('configuraciones/<int:configuracion_id>/editar/', views.configuracion_update, name='configuracion_update'),
    path('configuraciones/<int:configuracion_id>/eliminar/', views.configuracion_delete, name='configuracion_delete'),
    
    # URLs para Logs del Sistema
    path('logs/', views.logs_list, name='logs_list'),
    path('logs/<int:log_id>/', views.log_detail, name='log_detail'),
    path('logs/<int:log_id>/eliminar/', views.log_delete, name='log_delete'),
    path('logs/limpiar/', views.logs_limpiar, name='logs_limpiar'),
]



