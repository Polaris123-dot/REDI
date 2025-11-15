from django.contrib import admin
from .models import (
    Comunidad, Coleccion, TipoRecurso, EstadoDocumento, Licencia,
    Documento, VersionDocumento, Archivo, Autor, Colaborador,
    RelacionDocumento, EnlaceExterno, DerechoDocumento
)

class ArchivoInline(admin.TabularInline):
    """Permite editar archivos directamente desde la versión del documento."""
    model = Archivo
    extra = 1  # Cuántos formularios de archivo extra mostrar
    fields = ('archivo', 'nombre_original', 'tipo_mime', 'tamaño_bytes', 'es_archivo_principal')
    readonly_fields = ('nombre_original', 'tipo_mime', 'tamaño_bytes')

class VersionDocumentoInline(admin.TabularInline):
    """Permite editar versiones directamente desde el documento."""
    model = VersionDocumento
    extra = 1
    fields = ('numero_version', 'notas_version', 'creado_por', 'es_version_actual')
    readonly_fields = ('creado_por',)

@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    """Admin para el modelo Documento."""
    list_display = ('get_titulo', 'proyecto', 'creador', 'fecha_publicacion', 'visibilidad', 'estado')
    list_filter = ('visibilidad', 'estado', 'tipo_recurso', 'coleccion', 'fecha_publicacion')
    search_fields = ('titulo', 'resumen', 'proyecto__titulo', 'creador__username')
    inlines = [VersionDocumentoInline]
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    fieldsets = (
        (None, {
            'fields': ('proyecto', 'titulo', 'resumen', 'creador')
        }),
        ('Clasificación', {
            'fields': ('coleccion', 'tipo_recurso', 'estado', 'visibilidad', 'licencia')
        }),
        ('Fechas', {
            'fields': ('fecha_publicacion', 'fecha_aceptacion', 'fecha_publicacion_disponible')
        }),
        ('Identificadores', {
            'fields': ('handle', 'doi', 'isbn', 'issn')
        }),
        ('Metadatos Adicionales', {
            'classes': ('collapse',),
            'fields': ('idioma', 'palabras_clave', 'temas', 'campos_personalizados'),
        }),
    )

    def get_titulo(self, obj):
        return obj.get_titulo()
    get_titulo.short_description = 'Título'

@admin.register(VersionDocumento)
class VersionDocumentoAdmin(admin.ModelAdmin):
    """Admin para el modelo VersionDocumento."""
    list_display = ('__str__', 'documento', 'numero_version', 'creado_por', 'fecha_creacion', 'es_version_actual')
    list_filter = ('es_version_actual', 'documento__coleccion')
    search_fields = ('documento__titulo', 'notas_version')
    inlines = [ArchivoInline]

@admin.register(Archivo)
class ArchivoAdmin(admin.ModelAdmin):
    """Admin para el modelo Archivo."""
    list_display = ('nombre_original', 'version', 'tipo_mime', 'tamaño_bytes', 'fecha_subida', 'es_archivo_principal')
    list_filter = ('tipo_mime', 'es_archivo_principal')
    search_fields = ('nombre_original', 'version__documento__titulo')
    readonly_fields = ('nombre_original', 'tamaño_bytes', 'tipo_mime', 'fecha_subida')

# Registrar otros modelos para que sean visibles en el admin
admin.site.register(Comunidad)
admin.site.register(Coleccion)
admin.site.register(TipoRecurso)
admin.site.register(EstadoDocumento)
admin.site.register(Licencia)
admin.site.register(Autor)
admin.site.register(Colaborador)
admin.site.register(RelacionDocumento)
admin.site.register(EnlaceExterno)
admin.site.register(DerechoDocumento)