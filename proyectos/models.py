from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


class TipoProyecto(models.Model):
    """
    Define los tipos de proyectos disponibles (Tesis, Monografía, Artículo Científico, etc.).
    Cada tipo de proyecto tiene sus propios campos dinámicos.
    """
    nombre = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    descripcion = models.TextField(null=True, blank=True)
    icono = models.CharField(max_length=100, null=True, blank=True)
    color = models.CharField(max_length=7, null=True, blank=True, help_text='Color en formato hexadecimal')
    plantilla_vista = models.CharField(max_length=500, null=True, blank=True)
    es_activo = models.BooleanField(default=True)
    orden = models.PositiveIntegerField(default=0)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'tipos_proyecto'
        verbose_name = 'Tipo de Proyecto'
        verbose_name_plural = 'Tipos de Proyecto'
        ordering = ['orden', 'nombre']
        indexes = [
            models.Index(fields=['slug'], name='idx_tipos_proyecto_slug'),
            models.Index(fields=['es_activo'], name='idx_tipos_proyecto_activo'),
        ]
    
    def __str__(self):
        return self.nombre
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)


class CampoTipoProyecto(models.Model):
    """
    Define los campos dinámicos para cada tipo de proyecto.
    Permite configurar qué campos debe tener cada tipo de proyecto.
    """
    TIPO_DATO_CHOICES = [
        ('texto', 'Texto'),
        ('textarea', 'Área de Texto'),
        ('numero', 'Número'),
        ('fecha', 'Fecha'),
        ('booleano', 'Booleano'),
        ('select', 'Selección Única'),
        ('multiselect', 'Selección Múltiple'),
        ('archivo', 'Archivo'),
        ('url', 'URL'),
        ('email', 'Email'),
        ('json', 'JSON'),
    ]
    
    tipo_proyecto = models.ForeignKey(
        TipoProyecto,
        on_delete=models.CASCADE,
        related_name='campos',
        db_column='tipo_proyecto_id'
    )
    nombre = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    etiqueta = models.CharField(max_length=255)
    descripcion = models.TextField(null=True, blank=True)
    tipo_dato = models.CharField(
        max_length=20,
        choices=TIPO_DATO_CHOICES,
        default='texto'
    )
    es_obligatorio = models.BooleanField(default=False)
    es_repetible = models.BooleanField(default=False, help_text='Permite múltiples valores para este campo')
    es_buscable = models.BooleanField(default=True)
    es_indexable = models.BooleanField(default=True)
    orden = models.PositiveIntegerField(default=0)
    valores_posibles = models.JSONField(
        null=True,
        blank=True,
        help_text='Opciones para select/multiselect'
    )
    validador = models.CharField(max_length=255, null=True, blank=True, help_text='Regex o validación')
    valor_por_defecto = models.TextField(null=True, blank=True)
    ayuda = models.TextField(null=True, blank=True)
    categoria = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text='Agrupa campos en secciones'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'campos_tipo_proyecto'
        verbose_name = 'Campo de Tipo de Proyecto'
        verbose_name_plural = 'Campos de Tipo de Proyecto'
        unique_together = [['tipo_proyecto', 'slug']]
        ordering = ['tipo_proyecto', 'orden', 'categoria', 'nombre']
        indexes = [
            models.Index(fields=['tipo_proyecto'], name='idx_campos_tipo_proyecto_tipo'),
            models.Index(fields=['orden'], name='idx_campos_tipo_proyecto_orden'),
        ]
    
    def __str__(self):
        return f"{self.tipo_proyecto.nombre} - {self.etiqueta}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)


class Proyecto(models.Model):
    """
    Modelo principal de proyectos con campos dinámicos basados en TipoProyecto.
    Los valores específicos se almacenan en ValorCampoProyecto (EAV).
    """
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('en_revision', 'En Revisión'),
        ('aprobado', 'Aprobado'),
        ('publicado', 'Publicado'),
        ('archivado', 'Archivado'),
        ('rechazado', 'Rechazado'),
    ]
    
    VISIBILIDAD_CHOICES = [
        ('publico', 'Público'),
        ('privado', 'Privado'),
        ('restringido', 'Restringido'),
    ]
    
    titulo = models.CharField(max_length=500)
    slug = models.SlugField(max_length=500, unique=True)
    tipo_proyecto = models.ForeignKey(
        TipoProyecto,
        on_delete=models.RESTRICT,
        related_name='proyectos',
        db_column='tipo_proyecto_id'
    )
    creador = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        related_name='proyectos_creados',
        db_column='creador_id'
    )
    resumen = models.TextField(null=True, blank=True)
    descripcion = models.TextField(null=True, blank=True)
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='borrador'
    )
    visibilidad = models.CharField(
        max_length=20,
        choices=VISIBILIDAD_CHOICES,
        default='publico'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    fecha_publicacion = models.DateTimeField(null=True, blank=True)
    version = models.PositiveIntegerField(default=1)
    metadata_adicional = models.JSONField(
        null=True,
        blank=True,
        help_text='Metadata adicional en formato JSON'
    )
    
    # Relación OneToOne con Documento (para el PDF)
    # Se define en repositorio/models.py para evitar dependencia circular
    
    # Relaciones ManyToMany con categorías y etiquetas
    categorias = models.ManyToManyField(
        'catalogacion.Categoria',
        through='ProyectoCategoria',
        related_name='proyectos',
        blank=True
    )
    etiquetas = models.ManyToManyField(
        'catalogacion.Etiqueta',
        through='ProyectoEtiqueta',
        related_name='proyectos',
        blank=True
    )
    
    class Meta:
        db_table = 'proyectos'
        verbose_name = 'Proyecto'
        verbose_name_plural = 'Proyectos'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['titulo'], name='idx_proyectos_titulo'),
            models.Index(fields=['tipo_proyecto'], name='idx_proyectos_tipo'),
            models.Index(fields=['creador'], name='idx_proyectos_creador'),
            models.Index(fields=['estado'], name='idx_proyectos_estado'),
            models.Index(fields=['fecha_publicacion'], name='idx_proyectos_fecha_pub'),
        ]
    
    def __str__(self):
        return self.titulo
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titulo)
        super().save(*args, **kwargs)
    
    def get_valor_campo(self, campo_slug):
        """
        Obtiene el valor de un campo dinámico por su slug.
        Retorna el primer valor si es repetible, None si no existe.
        """
        try:
            campo = self.tipo_proyecto.campos.get(slug=campo_slug)
            valor = self.valores_campos.filter(
                campo_tipo_proyecto=campo
            ).first()
            if valor:
                return valor.get_valor()
            return None
        except CampoTipoProyecto.DoesNotExist:
            return None
    
    def get_valores_campo(self, campo_slug):
        """
        Obtiene todos los valores de un campo repetible.
        Retorna una lista de valores.
        """
        try:
            campo = self.tipo_proyecto.campos.get(slug=campo_slug)
            valores = self.valores_campos.filter(
                campo_tipo_proyecto=campo
            ).order_by('orden')
            return [v.get_valor() for v in valores]
        except CampoTipoProyecto.DoesNotExist:
            return []


class ValorCampoProyecto(models.Model):
    """
    Almacena los valores de los campos dinámicos de un proyecto (EAV).
    Cada campo puede tener múltiples valores si es repetible.
    """
    proyecto = models.ForeignKey(
        Proyecto,
        on_delete=models.CASCADE,
        related_name='valores_campos',
        db_column='proyecto_id'
    )
    campo_tipo_proyecto = models.ForeignKey(
        CampoTipoProyecto,
        on_delete=models.CASCADE,
        related_name='valores',
        db_column='campo_tipo_proyecto_id'
    )
    valor_texto = models.TextField(null=True, blank=True)
    valor_numero = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    valor_fecha = models.DateField(null=True, blank=True)
    valor_datetime = models.DateTimeField(null=True, blank=True)
    valor_booleano = models.BooleanField(null=True, blank=True)
    valor_json = models.JSONField(null=True, blank=True)
    valor_archivo = models.CharField(max_length=1000, null=True, blank=True)
    orden = models.PositiveIntegerField(default=0, help_text='Para campos repetibles')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'valores_campo_proyecto'
        verbose_name = 'Valor de Campo de Proyecto'
        verbose_name_plural = 'Valores de Campos de Proyecto'
        ordering = ['proyecto', 'campo_tipo_proyecto', 'orden']
        indexes = [
            models.Index(fields=['proyecto'], name='idx_valores_campo_proyecto'),
            models.Index(fields=['campo_tipo_proyecto'], name='idx_valores_campo_campo'),
            models.Index(fields=['valor_texto'], name='idx_valores_campo_texto'),
            models.Index(fields=['valor_numero'], name='idx_valores_campo_numero'),
            models.Index(fields=['valor_fecha'], name='idx_valores_campo_fecha'),
        ]
    
    def __str__(self):
        return f"{self.proyecto} - {self.campo_tipo_proyecto.etiqueta}"
    
    def get_valor(self):
        """
        Retorna el valor apropiado según el tipo de dato del campo.
        """
        tipo_dato = self.campo_tipo_proyecto.tipo_dato
        
        if tipo_dato == 'texto' or tipo_dato == 'textarea':
            return self.valor_texto
        elif tipo_dato == 'numero':
            return self.valor_numero
        elif tipo_dato == 'fecha':
            return self.valor_fecha
        elif tipo_dato == 'booleano':
            return self.valor_booleano
        elif tipo_dato in ['select', 'multiselect']:
            return self.valor_texto  # Los selects se almacenan como texto
        elif tipo_dato == 'archivo':
            return self.valor_archivo
        elif tipo_dato == 'url' or tipo_dato == 'email':
            return self.valor_texto
        elif tipo_dato == 'json':
            return self.valor_json
        
        return self.valor_texto
    
    def set_valor(self, valor):
        """
        Establece el valor apropiado según el tipo de dato del campo.
        """
        tipo_dato = self.campo_tipo_proyecto.tipo_dato
        
        # Limpiar todos los campos primero
        self.valor_texto = None
        self.valor_numero = None
        self.valor_fecha = None
        self.valor_datetime = None
        self.valor_booleano = None
        self.valor_json = None
        self.valor_archivo = None
        
        if tipo_dato == 'texto' or tipo_dato == 'textarea' or tipo_dato == 'url' or tipo_dato == 'email':
            self.valor_texto = str(valor) if valor is not None else None
        elif tipo_dato == 'numero':
            self.valor_numero = valor
        elif tipo_dato == 'fecha':
            self.valor_fecha = valor
        elif tipo_dato == 'booleano':
            self.valor_booleano = bool(valor) if valor is not None else None
        elif tipo_dato in ['select', 'multiselect']:
            self.valor_texto = str(valor) if valor is not None else None
        elif tipo_dato == 'archivo':
            self.valor_archivo = str(valor) if valor is not None else None
        elif tipo_dato == 'json':
            self.valor_json = valor


# Modelos ManyToMany para proyectos
class ProyectoCategoria(models.Model):
    """Relación ManyToMany entre Proyecto y Categoria"""
    proyecto = models.ForeignKey(
        Proyecto,
        on_delete=models.CASCADE,
        db_column='proyecto_id'
    )
    categoria = models.ForeignKey(
        'catalogacion.Categoria',
        on_delete=models.CASCADE,
        db_column='categoria_id'
    )
    
    class Meta:
        db_table = 'proyecto_categorias'
        verbose_name = 'Categoría de Proyecto'
        verbose_name_plural = 'Categorías de Proyectos'
        unique_together = [['proyecto', 'categoria']]
        indexes = [
            models.Index(fields=['proyecto'], name='idx_proy_cat_proy'),
            models.Index(fields=['categoria'], name='idx_proy_cat_cat'),
        ]
    
    def __str__(self):
        return f"{self.proyecto} - {self.categoria}"


class ProyectoEtiqueta(models.Model):
    """Relación ManyToMany entre Proyecto y Etiqueta"""
    proyecto = models.ForeignKey(
        Proyecto,
        on_delete=models.CASCADE,
        db_column='proyecto_id'
    )
    etiqueta = models.ForeignKey(
        'catalogacion.Etiqueta',
        on_delete=models.CASCADE,
        db_column='etiqueta_id'
    )
    
    class Meta:
        db_table = 'proyecto_etiquetas'
        verbose_name = 'Etiqueta de Proyecto'
        verbose_name_plural = 'Etiquetas de Proyectos'
        unique_together = [['proyecto', 'etiqueta']]
        indexes = [
            models.Index(fields=['proyecto'], name='idx_proy_etiq_proy'),
            models.Index(fields=['etiqueta'], name='idx_proy_etiq_etiq'),
        ]
    
    def __str__(self):
        return f"{self.proyecto} - {self.etiqueta}"


class ProyectoAutor(models.Model):
    """
    Autores de proyectos de investigación.
    Los autores deben ser usuarios del sistema (auth_user).
    Un proyecto puede tener múltiples autores (usuarios).
    """
    proyecto = models.ForeignKey(
        Proyecto,
        on_delete=models.CASCADE,
        related_name='autores',
        db_column='proyecto_id'
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='autoria_proyectos',
        db_column='usuario_id',
        help_text='Usuario del sistema (obligatorio)'
    )
    # Campos adicionales opcionales que pueden sobrescribir los del usuario
    afiliacion = models.CharField(max_length=500, null=True, blank=True, help_text='Institución o afiliación (opcional, si no se proporciona se usa la del usuario)')
    orcid_id = models.CharField(max_length=19, null=True, blank=True, help_text='ID de ORCID (opcional, si no se proporciona se usa la del usuario)')
    orden_autor = models.PositiveIntegerField(default=1, help_text='Orden de autoría (1 = primer autor)')
    es_correspondiente = models.BooleanField(default=False, help_text='Autor de correspondencia')
    es_autor_principal = models.BooleanField(default=False, help_text='Autor principal')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'proyecto_autores'
        verbose_name = 'Autor de Proyecto'
        verbose_name_plural = 'Autores de Proyectos'
        ordering = ['proyecto', 'orden_autor']
        unique_together = [['proyecto', 'usuario']]  # Un usuario solo puede ser autor una vez por proyecto
        indexes = [
            models.Index(fields=['proyecto'], name='idx_proyecto_autores_proyecto'),
            models.Index(fields=['usuario'], name='idx_proyecto_autores_usuario'),
            models.Index(fields=['orden_autor'], name='idx_proyecto_autores_orden'),
            models.Index(fields=['orcid_id'], name='idx_proyecto_autores_orcid'),
        ]
    
    def __str__(self):
        return f"{self.get_nombre_completo()} - {self.proyecto.titulo}"
    
    def get_nombre_completo(self):
        """Retorna el nombre completo del autor desde el usuario"""
        if self.usuario:
            return self.usuario.get_full_name() or self.usuario.username
        return "Usuario desconocido"
    
    def get_nombre(self):
        """Retorna el nombre del autor desde el usuario"""
        if self.usuario:
            return self.usuario.first_name or self.usuario.username
        return ""
    
    def get_apellidos(self):
        """Retorna los apellidos del autor desde el usuario"""
        if self.usuario:
            return self.usuario.last_name or ""
        return ""
    
    def get_email(self):
        """Retorna el email del autor desde el usuario"""
        if self.usuario:
            return self.usuario.email or ""
        return ""
    
    def get_afiliacion(self):
        """Retorna la afiliación, usando la del usuario si no hay una específica"""
        if self.afiliacion:
            return self.afiliacion
        # Intentar obtener desde el modelo Persona si existe
        if hasattr(self.usuario, 'persona'):
            return self.usuario.persona.institucion or ""
        return ""
    
    def get_orcid_id(self):
        """Retorna el ORCID ID, usando el del usuario si no hay uno específico"""
        if self.orcid_id:
            return self.orcid_id
        # Intentar obtener desde el modelo Persona si existe
        if hasattr(self.usuario, 'persona'):
            return self.usuario.persona.orcid_id or ""
        return ""
