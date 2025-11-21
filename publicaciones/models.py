from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from catalogacion.models import Categoria, Etiqueta


class Publicacion(models.Model):
    """
    Modelo de publicación que agrupa proyectos/documentos para publicar.
    """
    TIPO_PUBLICACION_CHOICES = [
        ('revista', 'Revista'),
        ('libro', 'Libro'),
        ('congreso', 'Congreso'),
        ('repositorio', 'Repositorio'),
        ('otro', 'Otro'),
    ]
    
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('en_proceso', 'En Proceso'),
        ('publicada', 'Publicada'),
        ('archivada', 'Archivada'),
    ]
    
    VISIBILIDAD_CHOICES = [
        ('publico', 'Público'),
        ('privado', 'Privado'),
        ('restringido', 'Restringido'),
    ]
    
    titulo = models.CharField(max_length=500, null=True, blank=True)
    slug = models.SlugField(max_length=255, unique=True)
    descripcion = models.TextField(null=True, blank=True)
    tipo_publicacion = models.CharField(
        max_length=20,
        choices=TIPO_PUBLICACION_CHOICES,
        default='repositorio'
    )
    editor = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        related_name='publicaciones_editadas',
        db_column='editor_id',
        help_text='Usuario que gestiona la publicación'
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='borrador'
    )
    visibilidad = models.CharField(
        max_length=20,
        choices=VISIBILIDAD_CHOICES,
        default='publico',
        help_text='Controla si la publicación es visible para el público general'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    fecha_publicacion = models.DateTimeField(null=True, blank=True)
    issn = models.CharField(max_length=20, null=True, blank=True)
    isbn = models.CharField(max_length=20, null=True, blank=True)
    doi = models.CharField(max_length=255, null=True, blank=True, unique=True)
    url_externa = models.URLField(max_length=1000, null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)
    
    # Relaciones ManyToMany
    proyectos = models.ManyToManyField(
        'proyectos.Proyecto',
        through='PublicacionProyecto',
        related_name='publicaciones',
        blank=True
    )
    categorias = models.ManyToManyField(
        Categoria,
        through='catalogacion.PublicacionCategoria',
        related_name='publicaciones',
        blank=True
    )
    etiquetas = models.ManyToManyField(
        Etiqueta,
        through='catalogacion.PublicacionEtiqueta',
        related_name='publicaciones',
        blank=True
    )
    
    class Meta:
        db_table = 'publicaciones'
        verbose_name = 'Publicación'
        verbose_name_plural = 'Publicaciones'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['slug'], name='idx_publicaciones_slug'),
            models.Index(fields=['editor'], name='idx_publicaciones_editor'),
            models.Index(fields=['estado'], name='idx_publicaciones_estado'),
            models.Index(fields=['visibilidad'], name='idx_publicaciones_visibilidad'),
            models.Index(fields=['doi'], name='idx_publicaciones_doi'),
        ]
    
    def __str__(self):
        return self.titulo
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titulo)
        super().save(*args, **kwargs)


class PublicacionProyecto(models.Model):
    """
    Relación ManyToMany entre Publicacion y Proyecto con metadata adicional.
    """
    publicacion = models.ForeignKey(
        Publicacion,
        on_delete=models.CASCADE,
        related_name='proyectos_relacionados',
        db_column='publicacion_id'
    )
    proyecto = models.ForeignKey(
        'proyectos.Proyecto',
        on_delete=models.CASCADE,
        related_name='publicaciones_relacionadas',
        db_column='proyecto_id'
    )
    orden = models.PositiveIntegerField(default=0)
    rol_en_publicacion = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text='artículo principal, capítulo, etc.'
    )
    fecha_incorporacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'publicacion_proyectos'
        verbose_name = 'Proyecto de Publicación'
        verbose_name_plural = 'Proyectos de Publicaciones'
        unique_together = [['publicacion', 'proyecto']]
        ordering = ['publicacion', 'orden']
        indexes = [
            models.Index(fields=['publicacion'], name='idx_pub_proyecto_publicacion'),
            models.Index(fields=['proyecto'], name='idx_pub_proyecto_proyecto'),
        ]
    
    def __str__(self):
        return f"{self.publicacion} - {self.proyecto}"
