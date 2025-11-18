from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from catalogacion.models import Categoria, Etiqueta


class Comunidad(models.Model):
    """
    Comunidades que agrupan colecciones de documentos.
    Permite crear una estructura jerárquica de repositorios.
    """
    ESTADO_CHOICES = [
        ('activa', 'Activa'),
        ('inactiva', 'Inactiva'),
        ('archivada', 'Archivada'),
    ]
    
    nombre = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    descripcion = models.TextField(null=True, blank=True)
    logo = models.CharField(max_length=500, null=True, blank=True)
    banner = models.CharField(max_length=500, null=True, blank=True)
    comunidad_padre = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subcomunidades',
        db_column='comunidad_padre_id'
    )
    administrador = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        related_name='comunidades_administradas',
        db_column='administrador_id'
    )
    es_publica = models.BooleanField(default=True)
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='activa'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'comunidades'
        verbose_name = 'Comunidad'
        verbose_name_plural = 'Comunidades'
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['slug'], name='idx_comunidades_slug'),
            models.Index(fields=['comunidad_padre'], name='idx_comunidad_padre'),
            models.Index(fields=['administrador'], name='idx_administrador'),
        ]
    
    def __str__(self):
        return self.nombre
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)


class Coleccion(models.Model):
    """
    Colecciones dentro de comunidades que agrupan documentos.
    Pueden tener jerarquía mediante coleccion_padre.
    """
    POLITICA_INGRESO_CHOICES = [
        ('abierto', 'Abierto'),
        ('cerrado', 'Cerrado'),
        ('revision', 'Requiere Revisión'),
    ]
    
    nombre = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    descripcion = models.TextField(null=True, blank=True)
    comunidad = models.ForeignKey(
        Comunidad,
        on_delete=models.CASCADE,
        related_name='colecciones',
        db_column='comunidad_id'
    )
    coleccion_padre = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subcolecciones',
        db_column='coleccion_padre_id'
    )
    administrador = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        related_name='colecciones_administradas',
        db_column='administrador_id'
    )
    politica_ingreso = models.CharField(
        max_length=20,
        choices=POLITICA_INGRESO_CHOICES,
        default='abierto'
    )
    es_publica = models.BooleanField(default=True)
    plantilla_metadatos = models.JSONField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'colecciones'
        verbose_name = 'Colección'
        verbose_name_plural = 'Colecciones'
        unique_together = [['slug', 'comunidad']]
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['comunidad'], name='idx_colecciones_comunidad'),
            models.Index(fields=['coleccion_padre'], name='idx_colecciones_padre'),
            models.Index(fields=['administrador'], name='idx_colecciones_admin'),
        ]
    
    def __str__(self):
        return f"{self.comunidad.nombre} - {self.nombre}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)


class TipoRecurso(models.Model):
    """
    Tipos de recursos/documentos (Artículo, Tesis, Libro, etc.).
    """
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(null=True, blank=True)
    icono = models.CharField(max_length=100, null=True, blank=True)
    categoria = models.CharField(max_length=50, null=True, blank=True)
    
    class Meta:
        db_table = 'tipos_recurso'
        verbose_name = 'Tipo de Recurso'
        verbose_name_plural = 'Tipos de Recurso'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre


class EstadoDocumento(models.Model):
    """
    Estados posibles de un documento (Borrador, Publicado, etc.).
    """
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(null=True, blank=True)
    orden = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'estados_documento'
        verbose_name = 'Estado de Documento'
        verbose_name_plural = 'Estados de Documento'
        ordering = ['orden', 'nombre']
    
    def __str__(self):
        return self.nombre


class Licencia(models.Model):
    """
    Licencias que pueden aplicarse a documentos.
    """
    nombre = models.CharField(max_length=255)
    codigo = models.CharField(max_length=100, unique=True)
    version = models.CharField(max_length=20, null=True, blank=True)
    url = models.CharField(max_length=500, null=True, blank=True)
    descripcion = models.TextField(null=True, blank=True)
    permite_comercial = models.BooleanField(default=False)
    permite_modificacion = models.BooleanField(default=False)
    requiere_attribucion = models.BooleanField(default=True)
    texto_completo = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'licencias'
        verbose_name = 'Licencia'
        verbose_name_plural = 'Licencias'
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['codigo'], name='idx_licencias_codigo'),
        ]
    
    def __str__(self):
        return self.nombre


class Documento(models.Model):
    """
    Modelo de documentos del repositorio.
    Almacena principalmente el archivo PDF y metadatos opcionales.
    El título y descripción vienen del Proyecto asociado.
    """
    VISIBILIDAD_CHOICES = [
        ('publico', 'Público'),
        ('privado', 'Privado'),
        ('restringido', 'Restringido'),
    ]
    
    # Relación con Proyecto (opcional, pero recomendado)
    proyecto = models.OneToOneField(
        'proyectos.Proyecto',
        on_delete=models.CASCADE,
        related_name='documento',
        null=True,
        blank=True,
        db_column='proyecto_id',
        help_text='Proyecto asociado a este documento. El título y descripción vienen del proyecto.'
    )
    
    handle = models.CharField(max_length=255, unique=True, null=True, blank=True, help_text='Identificador único permanente (se genera automáticamente si no se proporciona)')
    titulo = models.CharField(max_length=500, null=True, blank=True, help_text='Título opcional. Si hay proyecto asociado, se usa el título del proyecto.')
    resumen = models.TextField(null=True, blank=True, help_text='Resumen opcional. Si hay proyecto asociado, se usa el resumen del proyecto.')
    tipo_recurso = models.ForeignKey(
        TipoRecurso,
        on_delete=models.RESTRICT,
        related_name='documentos',
        db_column='tipo_recurso_id',
        null=True,
        blank=True
    )
    coleccion = models.ForeignKey(
        Coleccion,
        on_delete=models.RESTRICT,
        related_name='documentos',
        db_column='coleccion_id',
        null=True,
        blank=True
    )
    creador = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        related_name='documentos_creados',
        db_column='creador_id'
    )
    estado = models.ForeignKey(
        EstadoDocumento,
        on_delete=models.RESTRICT,
        related_name='documentos',
        db_column='estado_id',
        null=True,
        blank=True
    )
    idioma = models.CharField(max_length=10, default='es')
    fecha_publicacion = models.DateField(null=True, blank=True)
    fecha_aceptacion = models.DateField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    fecha_publicacion_disponible = models.DateTimeField(null=True, blank=True)
    visibilidad = models.CharField(
        max_length=20,
        choices=VISIBILIDAD_CHOICES,
        default='publico'
    )
    version_actual = models.PositiveIntegerField(default=1)
    numero_acceso = models.CharField(max_length=50, null=True, blank=True)
    doi = models.CharField(max_length=255, null=True, blank=True, unique=True)
    isbn = models.CharField(max_length=20, null=True, blank=True)
    issn = models.CharField(max_length=20, null=True, blank=True)
    licencia = models.ForeignKey(
        Licencia,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documentos',
        db_column='licencia_id'
    )
    palabras_clave = models.TextField(null=True, blank=True)
    temas = models.JSONField(null=True, blank=True)
    campos_personalizados = models.JSONField(null=True, blank=True)
    metadata_completa = models.JSONField(null=True, blank=True)
    
    # Relaciones ManyToMany con categorías y etiquetas
    categorias = models.ManyToManyField(
        Categoria,
        through='catalogacion.DocumentoCategoria',
        related_name='documentos',
        blank=True
    )
    etiquetas = models.ManyToManyField(
        Etiqueta,
        through='catalogacion.DocumentoEtiqueta',
        related_name='documentos',
        blank=True
    )
    
    class Meta:
        db_table = 'documentos'
        verbose_name = 'Documento'
        verbose_name_plural = 'Documentos'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['handle'], name='idx_documentos_handle'),
            models.Index(fields=['titulo'], name='idx_documentos_titulo'),
            models.Index(fields=['tipo_recurso'], name='idx_documentos_tipo_recurso'),
            models.Index(fields=['coleccion'], name='idx_documentos_coleccion'),
            models.Index(fields=['creador'], name='idx_documentos_creador'),
            models.Index(fields=['estado'], name='idx_documentos_estado'),
            models.Index(fields=['doi'], name='idx_documentos_doi'),
            models.Index(fields=['fecha_publicacion'], name='idx_documentos_fecha_pub'),
        ]
    
    def __str__(self):
        if self.proyecto:
            return f"Documento de: {self.proyecto.titulo}"
        return self.titulo or f"Documento #{self.id}"
    
    def get_titulo(self):
        """Retorna el título del proyecto si existe, sino el título del documento"""
        if self.proyecto:
            return self.proyecto.titulo
        return self.titulo or f"Documento #{self.id}"
    
    def get_resumen(self):
        """Retorna el resumen del proyecto si existe, sino el resumen del documento"""
        if self.proyecto:
            return self.proyecto.resumen
        return self.resumen


class VersionDocumento(models.Model):
    """
    Versiones de un documento.
    Cada documento puede tener múltiples versiones.
    """
    documento = models.ForeignKey(
        Documento,
        on_delete=models.CASCADE,
        related_name='versiones',
        db_column='documento_id'
    )
    numero_version = models.PositiveIntegerField()
    notas_version = models.TextField(null=True, blank=True)
    creado_por = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        related_name='versiones_creadas',
        db_column='creado_por'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    es_version_actual = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'versiones_documento'
        verbose_name = 'Versión de Documento'
        verbose_name_plural = 'Versiones de Documento'
        unique_together = [['documento', 'numero_version']]
        ordering = ['documento', '-numero_version']
        indexes = [
            models.Index(fields=['documento'], name='idx_versiones_doc_documento'),
            models.Index(fields=['creado_por'], name='idx_versiones_doc_creado_por'),
        ]
    
    def __str__(self):
        doc_titulo = self.documento.get_titulo() if hasattr(self.documento, 'get_titulo') else (self.documento.titulo or f"Doc #{self.documento.id}")
        return f"{doc_titulo} - v{self.numero_version}"


def archivo_upload_path(instance, filename):
    """
    Genera la ruta de almacenamiento para el archivo.
    Usa IDs en lugar de handles para evitar caracteres inválidos en Windows.
    """
    import os
    import re
    
    # Sanitizar el nombre del archivo (remover caracteres inválidos)
    def sanitize_filename(name):
        # Remover caracteres inválidos para Windows: < > : " | ? * \
        name = re.sub(r'[<>:"|?*\\]', '_', name)
        # Limitar longitud
        if len(name) > 200:
            name, ext = os.path.splitext(name)
            name = name[:200-len(ext)] + ext
        return name
    
    # Sanitizar el nombre del archivo
    safe_filename = sanitize_filename(filename)
    
    if instance.version and instance.version.documento:
        documento = instance.version.documento
        documento_id = documento.id
        version_num = instance.version.numero_version
        
        # Si hay proyecto, usar el ID del proyecto
        if documento.proyecto:
            proyecto_id = documento.proyecto.id
            return f'documentos/proyectos/proyecto_{proyecto_id}/doc_{documento_id}/v{version_num}/{safe_filename}'
        
        # Si no hay proyecto, usar solo el ID del documento
        return f'documentos/doc_{documento_id}/v{version_num}/{safe_filename}'
    
    # Fallback: usar timestamp para evitar colisiones
    import time
    timestamp = int(time.time())
    return f'documentos/genericos/{timestamp}/{safe_filename}'


class Archivo(models.Model):
    """
    Archivos asociados a versiones de documentos.
    Almacena principalmente PDFs de proyectos de investigación.
    """
    version = models.ForeignKey(
        VersionDocumento,
        on_delete=models.CASCADE,
        related_name='archivos',
        db_column='version_id'
    )
    # Campo de archivo real de Django
    archivo = models.FileField(
        upload_to=archivo_upload_path,
        max_length=1000,
        help_text='Archivo PDF del documento',
        null=True,
        blank=True
    )
    nombre_original = models.CharField(max_length=500, help_text='Nombre original del archivo subido')
    nombre_almacenado = models.CharField(max_length=500, null=True, blank=True, help_text='Nombre con el que se almacenó (deprecated, usar archivo)')
    ruta_completa = models.CharField(max_length=1000, null=True, blank=True, help_text='Ruta completa (deprecated, usar archivo)')
    tipo_mime = models.CharField(max_length=100, null=True, blank=True)
    tamaño_bytes = models.BigIntegerField(null=True, blank=True, help_text='Tamaño en bytes')
    checksum_md5 = models.CharField(max_length=32, null=True, blank=True)
    checksum_sha256 = models.CharField(max_length=64, null=True, blank=True)
    descripcion = models.TextField(null=True, blank=True)
    es_archivo_principal = models.BooleanField(default=False, help_text='Indica si es el archivo principal (PDF) del documento')
    formato = models.CharField(max_length=50, null=True, blank=True, help_text='Formato del archivo (pdf, doc, etc.)')
    numero_paginas = models.PositiveIntegerField(null=True, blank=True, help_text='Número de páginas (para PDFs)')
    resolucion = models.CharField(max_length=50, null=True, blank=True)
    duracion = models.PositiveIntegerField(null=True, blank=True, help_text='En segundos')
    bitrate = models.PositiveIntegerField(null=True, blank=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'archivos'
        verbose_name = 'Archivo'
        verbose_name_plural = 'Archivos'
        ordering = ['version', '-es_archivo_principal', 'fecha_subida']
        indexes = [
            models.Index(fields=['version'], name='idx_archivos_version'),
            models.Index(fields=['checksum_md5'], name='idx_archivos_checksum'),
            models.Index(fields=['tipo_mime'], name='idx_archivos_tipo_mime'),
        ]
    
    def __str__(self):
        if self.archivo:
            return f"{self.version} - {self.nombre_original} ({self.archivo.name})"
        return f"{self.version} - {self.nombre_original}"
    
    def get_url_archivo(self):
        """Retorna la URL del archivo si existe"""
        if self.archivo:
            return self.archivo.url
        return None
    
    def get_tamaño_formateado(self):
        """Retorna el tamaño del archivo formateado"""
        if self.tamaño_bytes:
            tamaño = self.tamaño_bytes
            for unit in ['B', 'KB', 'MB', 'GB']:
                if tamaño < 1024.0:
                    return f"{tamaño:.2f} {unit}"
                tamaño /= 1024.0
            return f"{tamaño:.2f} TB"
        return "N/A"


class Autor(models.Model):
    """
    Autores de documentos.
    Puede estar vinculado a un usuario o ser independiente.
    """
    documento = models.ForeignKey(
        Documento,
        on_delete=models.CASCADE,
        related_name='autores',
        db_column='documento_id'
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='autoria_documentos',
        db_column='usuario_id'
    )
    nombre = models.CharField(max_length=200)
    apellidos = models.CharField(max_length=200)
    email = models.EmailField(null=True, blank=True)
    afiliacion = models.CharField(max_length=500, null=True, blank=True)
    orcid_id = models.CharField(max_length=19, null=True, blank=True)
    orden_autor = models.PositiveIntegerField(default=1)
    es_correspondiente = models.BooleanField(default=False)
    es_autor_principal = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'autores'
        verbose_name = 'Autor'
        verbose_name_plural = 'Autores'
        ordering = ['documento', 'orden_autor']
        indexes = [
            models.Index(fields=['documento'], name='idx_autores_documento'),
            models.Index(fields=['usuario'], name='idx_autores_usuario'),
            models.Index(fields=['orden_autor'], name='idx_autores_orden'),
        ]
    
    def __str__(self):
        return f"{self.nombre} {self.apellidos} - {self.documento.titulo}"


class Colaborador(models.Model):
    """
    Colaboradores de documentos (editores, revisores, etc.).
    """
    ROL_CHOICES = [
        ('editor', 'Editor'),
        ('revisor', 'Revisor'),
        ('colaborador', 'Colaborador'),
        ('supervisor', 'Supervisor'),
        ('patrocinador', 'Patrocinador'),
    ]
    
    documento = models.ForeignKey(
        Documento,
        on_delete=models.CASCADE,
        related_name='colaboradores',
        db_column='documento_id'
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='colaboraciones_documentos',
        db_column='usuario_id'
    )
    rol = models.CharField(
        max_length=20,
        choices=ROL_CHOICES
    )
    permisos = models.JSONField(null=True, blank=True)
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'colaboradores'
        verbose_name = 'Colaborador'
        verbose_name_plural = 'Colaboradores'
        ordering = ['documento', 'rol']
        indexes = [
            models.Index(fields=['documento'], name='idx_colaboradores_documento'),
            models.Index(fields=['usuario'], name='idx_colaboradores_usuario'),
        ]
    
    def __str__(self):
        return f"{self.usuario.get_full_name()} - {self.documento.titulo} ({self.rol})"


class RelacionDocumento(models.Model):
    """
    Relaciones entre documentos (versiones, citas, etc.).
    """
    TIPO_RELACION_CHOICES = [
        ('version_anterior', 'Versión Anterior'),
        ('version_posterior', 'Versión Posterior'),
        ('parte_de', 'Parte De'),
        ('contiene', 'Contiene'),
        ('relacionado', 'Relacionado'),
        ('suplementa', 'Suplementa'),
        ('cita', 'Cita'),
    ]
    
    documento_origen = models.ForeignKey(
        Documento,
        on_delete=models.CASCADE,
        related_name='relaciones_salientes',
        db_column='documento_origen_id'
    )
    documento_destino = models.ForeignKey(
        Documento,
        on_delete=models.CASCADE,
        related_name='relaciones_entrantes',
        db_column='documento_destino_id'
    )
    tipo_relacion = models.CharField(
        max_length=20,
        choices=TIPO_RELACION_CHOICES
    )
    descripcion = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'relaciones_documentos'
        verbose_name = 'Relación de Documento'
        verbose_name_plural = 'Relaciones de Documentos'
        unique_together = [['documento_origen', 'documento_destino', 'tipo_relacion']]
        indexes = [
            models.Index(fields=['documento_origen'], name='idx_relaciones_origen'),
            models.Index(fields=['documento_destino'], name='idx_relaciones_destino'),
        ]
    
    def __str__(self):
        return f"{self.documento_origen} - {self.get_tipo_relacion_display()} - {self.documento_destino}"


class EnlaceExterno(models.Model):
    """
    Enlaces externos relacionados con documentos.
    """
    TIPO_CHOICES = [
        ('repositorio', 'Repositorio'),
        ('preprint', 'Preprint'),
        ('version_publisher', 'Versión Publisher'),
        ('datos', 'Datos'),
        ('codigo', 'Código'),
        ('multimedia', 'Multimedia'),
        ('otros', 'Otros'),
    ]
    
    documento = models.ForeignKey(
        Documento,
        on_delete=models.CASCADE,
        related_name='enlaces_externos',
        db_column='documento_id'
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default='otros'
    )
    url = models.URLField(max_length=1000)
    titulo = models.CharField(max_length=500, null=True, blank=True)
    descripcion = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'enlaces_externos'
        verbose_name = 'Enlace Externo'
        verbose_name_plural = 'Enlaces Externos'
        ordering = ['documento', 'tipo']
        indexes = [
            models.Index(fields=['documento'], name='idx_enlaces_ext_documento'),
        ]
    
    def __str__(self):
        return f"{self.documento} - {self.get_tipo_display()}"


class DerechoDocumento(models.Model):
    """
    Derechos asociados a documentos (copyright, patentes, etc.).
    """
    TIPO_DERECHO_CHOICES = [
        ('copyright', 'Copyright'),
        ('patente', 'Patente'),
        ('marca', 'Marca'),
        ('privacidad', 'Privacidad'),
        ('otros', 'Otros'),
    ]
    
    documento = models.ForeignKey(
        Documento,
        on_delete=models.CASCADE,
        related_name='derechos',
        db_column='documento_id'
    )
    tipo_derecho = models.CharField(
        max_length=20,
        choices=TIPO_DERECHO_CHOICES
    )
    titular = models.CharField(max_length=500)
    descripcion = models.TextField(null=True, blank=True)
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)
    
    class Meta:
        db_table = 'derechos_documento'
        verbose_name = 'Derecho de Documento'
        verbose_name_plural = 'Derechos de Documentos'
        ordering = ['documento', 'tipo_derecho']
        indexes = [
            models.Index(fields=['documento'], name='idx_derechos_documento'),
        ]
    
    def __str__(self):
        return f"{self.documento} - {self.get_tipo_derecho_display()}"
