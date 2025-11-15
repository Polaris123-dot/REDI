from django.db import models
from repositorio.models import Documento


class EsquemaMetadatos(models.Model):
    """
    Esquemas de metadatos (Dublin Core, MARC, etc.).
    """
    nombre = models.CharField(max_length=100, unique=True)
    prefijo = models.CharField(max_length=50, unique=True)
    namespace = models.CharField(max_length=500)
    descripcion = models.TextField(null=True, blank=True)
    version = models.CharField(max_length=20, null=True, blank=True)
    
    class Meta:
        db_table = 'esquemas_metadatos'
        verbose_name = 'Esquema de Metadatos'
        verbose_name_plural = 'Esquemas de Metadatos'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre


class CampoMetadatos(models.Model):
    """
    Campos definidos en un esquema de metadatos.
    """
    TIPO_DATO_CHOICES = [
        ('texto', 'Texto'),
        ('numero', 'Número'),
        ('fecha', 'Fecha'),
        ('booleano', 'Booleano'),
        ('lista', 'Lista'),
        ('json', 'JSON'),
    ]
    
    esquema = models.ForeignKey(
        EsquemaMetadatos,
        on_delete=models.CASCADE,
        related_name='campos',
        db_column='esquema_id'
    )
    nombre = models.CharField(max_length=100)
    etiqueta = models.CharField(max_length=255)
    tipo_dato = models.CharField(
        max_length=20,
        choices=TIPO_DATO_CHOICES,
        default='texto'
    )
    es_obligatorio = models.BooleanField(default=False)
    es_repetible = models.BooleanField(default=False)
    valores_posibles = models.JSONField(null=True, blank=True)
    descripcion = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'campos_metadatos'
        verbose_name = 'Campo de Metadatos'
        verbose_name_plural = 'Campos de Metadatos'
        unique_together = [['esquema', 'nombre']]
        ordering = ['esquema', 'nombre']
        indexes = [
            models.Index(fields=['esquema'], name='idx_campos_metadatos_esquema'),
        ]
    
    def __str__(self):
        return f"{self.esquema.nombre} - {self.etiqueta}"


class MetadatoDocumento(models.Model):
    """
    Valores de metadatos para documentos.
    """
    documento = models.ForeignKey(
        Documento,
        on_delete=models.CASCADE,
        related_name='metadatos',
        db_column='documento_id'
    )
    campo_metadato = models.ForeignKey(
        CampoMetadatos,
        on_delete=models.CASCADE,
        related_name='valores',
        db_column='campo_metadato_id'
    )
    valor_texto = models.TextField(null=True, blank=True)
    valor_numero = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    valor_fecha = models.DateField(null=True, blank=True)
    valor_booleano = models.BooleanField(null=True, blank=True)
    valor_json = models.JSONField(null=True, blank=True)
    idioma = models.CharField(max_length=10, null=True, blank=True)
    orden = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'metadatos_documento'
        verbose_name = 'Metadato de Documento'
        verbose_name_plural = 'Metadatos de Documentos'
        ordering = ['documento', 'campo_metadato', 'orden']
        indexes = [
            models.Index(fields=['documento'], name='idx_metadatos_documento'),
            models.Index(fields=['campo_metadato'], name='idx_metadatos_campo'),
            models.Index(fields=['valor_texto'], name='idx_metadatos_valor_texto'),
        ]
    
    def __str__(self):
        return f"{self.documento} - {self.campo_metadato.etiqueta}"
    
    def get_valor(self):
        """Retorna el valor apropiado según el tipo de dato"""
        tipo_dato = self.campo_metadato.tipo_dato
        
        if tipo_dato == 'texto' or tipo_dato == 'lista':
            return self.valor_texto
        elif tipo_dato == 'numero':
            return self.valor_numero
        elif tipo_dato == 'fecha':
            return self.valor_fecha
        elif tipo_dato == 'booleano':
            return self.valor_booleano
        elif tipo_dato == 'json':
            return self.valor_json
        
        return self.valor_texto
