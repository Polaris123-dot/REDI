from django.urls import path
from . import views

app_name = 'catalogacion'

urlpatterns = [
    # Página principal de catalogación
    path('', views.index, name='index'),
    
    # URLs para Categorías
    path('categorias/', views.categorias_list, name='categorias_list'),
    path('categorias/crear/', views.categoria_create, name='categoria_create'),
    path('categorias/<int:categoria_id>/', views.categoria_detail, name='categoria_detail'),
    path('categorias/<int:categoria_id>/editar/', views.categoria_update, name='categoria_update'),
    path('categorias/<int:categoria_id>/eliminar/', views.categoria_delete, name='categoria_delete'),
    
    # URLs para Etiquetas
    path('etiquetas/', views.etiquetas_list, name='etiquetas_list'),
    path('etiquetas/crear/', views.etiqueta_create, name='etiqueta_create'),
    path('etiquetas/<int:etiqueta_id>/', views.etiqueta_detail, name='etiqueta_detail'),
    path('etiquetas/<int:etiqueta_id>/editar/', views.etiqueta_update, name='etiqueta_update'),
    path('etiquetas/<int:etiqueta_id>/eliminar/', views.etiqueta_delete, name='etiqueta_delete'),
]

