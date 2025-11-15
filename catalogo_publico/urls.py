from django.urls import path
from . import views

app_name = 'catalogo_publico'

urlpatterns = [
    # Página principal pública
    path('', views.index, name='index'),
    
    # Búsqueda
    path('buscar/', views.buscar, name='buscar'),
    
    # Detalle de publicación
    path('publicacion/<slug:slug>/', views.publicacion_detalle, name='publicacion_detalle'),
    
    # Descarga de documento
    path('descargar/<int:documento_id>/', views.descargar_documento, name='descargar_documento'),
    
    # Perfil de autor
    path('autor/<int:user_id>/', views.autor_perfil, name='autor_perfil'),
    
    # Categoría
    path('categoria/<slug:slug>/', views.categoria_proyectos, name='categoria_proyectos'),
    
    # URLs auxiliares para AJAX (filtros, búsqueda)
    path('buscar/ajax/', views.buscar_ajax, name='buscar_ajax'),
    path('filtros/opciones/', views.obtener_opciones_filtros, name='obtener_opciones_filtros'),
    path('filtros/tipos-proyecto/', views.obtener_tipos_proyecto, name='obtener_tipos_proyecto'),
    path('filtros/autores/', views.obtener_autores, name='obtener_autores'),
    path('filtros/categorias/', views.obtener_categorias, name='obtener_categorias'),
]


