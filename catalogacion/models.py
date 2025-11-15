from django.db import models
from django.utils.text import slugify
from django.core.exceptions import ValidationError


class Categoria(models.Model):
    """
    Modelo de categorías jerárquicas para organizar proyectos, documentos y publicaciones.
    Soporta categorías anidadas mediante auto-referencia.
    """
    nombre = models.CharField(max_length=255, verbose_name="Nombre")
    slug = models.SlugField(max_length=255, unique=True, verbose_name="Slug")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    categoria_padre = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='subcategorias',
        verbose_name="Categoría padre"
    )
    nivel = models.PositiveIntegerField(default=0, verbose_name="Nivel")
    ruta_completa = models.CharField(
        max_length=1000,
        blank=True,
        null=True,
        verbose_name="Ruta completa"
    )

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['nivel', 'nombre']
        indexes = [
            models.Index(fields=['slug'], name='idx_categoria_slug'),
            models.Index(fields=['categoria_padre'], name='idx_categoria_padre'),
        ]

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        
        # Calcular nivel y ruta completa
        if self.categoria_padre:
            self.nivel = self.categoria_padre.nivel + 1
            self.ruta_completa = f"{self.categoria_padre.ruta_completa or self.categoria_padre.nombre} > {self.nombre}"
        else:
            self.nivel = 0
            self.ruta_completa = self.nombre
        
        super().save(*args, **kwargs)
        
        # Actualizar ruta de subcategorías si cambió
        for subcategoria in self.subcategorias.all():
            subcategoria.save()

    def clean(self):
        # Evitar referencias circulares
        if self.categoria_padre:
            if self.categoria_padre == self:
                raise ValidationError("Una categoría no puede ser padre de sí misma.")
            # Verificar ancestros
            padre = self.categoria_padre
            while padre:
                if padre == self:
                    raise ValidationError("Referencia circular detectada en la jerarquía de categorías.")
                padre = padre.categoria_padre


class Etiqueta(models.Model):
    """
    Modelo de etiquetas para etiquetar proyectos, documentos y publicaciones.
    Las etiquetas son simples (sin jerarquía) y permiten búsqueda rápida.
    """
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="Slug")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    color = models.CharField(
        max_length=7,
        blank=True,
        null=True,
        verbose_name="Color",
        help_text="Color en formato hexadecimal (ej: #FF5733)"
    )

    class Meta:
        verbose_name = "Etiqueta"
        verbose_name_plural = "Etiquetas"
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['slug'], name='idx_etiqueta_slug'),
        ]

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)


# Modelos de relaciones ManyToMany
# Estos modelos intermedios permiten agregar metadata adicional si es necesario

class DocumentoCategoria(models.Model):
    """Relación ManyToMany entre Documento y Categoria"""
    documento = models.ForeignKey(
        'repositorio.Documento',
        on_delete=models.CASCADE,
        db_column='documento_id'
    )
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.CASCADE,
        db_column='categoria_id'
    )
    
    class Meta:
        db_table = 'documento_categorias'
        verbose_name = 'Categoría de Documento'
        verbose_name_plural = 'Categorías de Documentos'
        unique_together = [['documento', 'categoria']]
        indexes = [
            models.Index(fields=['documento'], name='idx_doc_categoria_documento'),
            models.Index(fields=['categoria'], name='idx_doc_categoria_categoria'),
        ]
    
    def __str__(self):
        return f"{self.documento} - {self.categoria}"


class DocumentoEtiqueta(models.Model):
    """Relación ManyToMany entre Documento y Etiqueta"""
    documento = models.ForeignKey(
        'repositorio.Documento',
        on_delete=models.CASCADE,
        db_column='documento_id'
    )
    etiqueta = models.ForeignKey(
        Etiqueta,
        on_delete=models.CASCADE,
        db_column='etiqueta_id'
    )
    
    class Meta:
        db_table = 'documento_etiquetas'
        verbose_name = 'Etiqueta de Documento'
        verbose_name_plural = 'Etiquetas de Documentos'
        unique_together = [['documento', 'etiqueta']]
        indexes = [
            models.Index(fields=['documento'], name='idx_doc_etiqueta_documento'),
            models.Index(fields=['etiqueta'], name='idx_doc_etiqueta_etiqueta'),
        ]
    
    def __str__(self):
        return f"{self.documento} - {self.etiqueta}"


class PublicacionCategoria(models.Model):
    """Relación ManyToMany entre Publicacion y Categoria"""
    publicacion = models.ForeignKey(
        'publicaciones.Publicacion',
        on_delete=models.CASCADE,
        db_column='publicacion_id'
    )
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.CASCADE,
        db_column='categoria_id'
    )
    
    class Meta:
        db_table = 'publicacion_categorias'
        verbose_name = 'Categoría de Publicación'
        verbose_name_plural = 'Categorías de Publicaciones'
        unique_together = [['publicacion', 'categoria']]
        indexes = [
            models.Index(fields=['publicacion'], name='idx_pub_categoria_publicacion'),
            models.Index(fields=['categoria'], name='idx_pub_categoria_categoria'),
        ]
    
    def __str__(self):
        return f"{self.publicacion} - {self.categoria}"


class PublicacionEtiqueta(models.Model):
    """Relación ManyToMany entre Publicacion y Etiqueta"""
    publicacion = models.ForeignKey(
        'publicaciones.Publicacion',
        on_delete=models.CASCADE,
        db_column='publicacion_id'
    )
    etiqueta = models.ForeignKey(
        Etiqueta,
        on_delete=models.CASCADE,
        db_column='etiqueta_id'
    )
    
    class Meta:
        db_table = 'publicacion_etiquetas'
        verbose_name = 'Etiqueta de Publicación'
        verbose_name_plural = 'Etiquetas de Publicaciones'
        unique_together = [['publicacion', 'etiqueta']]
        indexes = [
            models.Index(fields=['publicacion'], name='idx_pub_etiqueta_publicacion'),
            models.Index(fields=['etiqueta'], name='idx_pub_etiqueta_etiqueta'),
        ]
    
    def __str__(self):
        return f"{self.publicacion} - {self.etiqueta}"
