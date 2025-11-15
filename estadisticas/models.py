from django.db import models
from django.contrib.auth.models import User
from repositorio.models import Documento, Archivo


class VisitaDocumento(models.Model):
    """
    Registro de visitas a documentos.
    """
    TIPO_ACCESO_CHOICES = [
        ('vista', 'Vista'),
        ('descarga', 'Descarga'),
        ('preview', 'Preview'),
    ]
    
    documento = models.ForeignKey(
        Documento,
        on_delete=models.CASCADE,
        related_name='visitas',
        db_column='documento_id'
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='visitas_documentos',
        db_column='usuario_id'
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, null=True, blank=True)
    pais = models.CharField(max_length=2, null=True, blank=True)
    ciudad = models.CharField(max_length=100, null=True, blank=True)
    referer = models.CharField(max_length=1000, null=True, blank=True)
    tipo_acceso = models.CharField(
        max_length=20,
        choices=TIPO_ACCESO_CHOICES,
        default='vista'
    )
    fecha = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'visitas_documento'
        verbose_name = 'Visita de Documento'
        verbose_name_plural = 'Visitas de Documentos'
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['documento'], name='idx_visitas_documento'),
            models.Index(fields=['usuario'], name='idx_visitas_usuario'),
            models.Index(fields=['fecha'], name='idx_visitas_fecha'),
            models.Index(fields=['tipo_acceso'], name='idx_visitas_tipo_acceso'),
        ]
    
    def __str__(self):
        return f"{self.documento} - {self.fecha}"


class DescargaArchivo(models.Model):
    """
    Registro de descargas de archivos.
    """
    archivo = models.ForeignKey(
        Archivo,
        on_delete=models.CASCADE,
        related_name='descargas',
        db_column='archivo_id'
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='descargas_archivos',
        db_column='usuario_id'
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'descargas_archivo'
        verbose_name = 'Descarga de Archivo'
        verbose_name_plural = 'Descargas de Archivos'
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['archivo'], name='idx_descargas_archivo'),
            models.Index(fields=['usuario'], name='idx_descargas_usuario'),
            models.Index(fields=['fecha'], name='idx_descargas_fecha'),
        ]
    
    def __str__(self):
        return f"{self.archivo} - {self.fecha}"


class EstadisticaAgregada(models.Model):
    """
    Estadísticas agregadas por período.
    """
    PERIODO_CHOICES = [
        ('diario', 'Diario'),
        ('semanal', 'Semanal'),
        ('mensual', 'Mensual'),
        ('anual', 'Anual'),
    ]
    
    documento = models.ForeignKey(
        Documento,
        on_delete=models.CASCADE,
        related_name='estadisticas_agregadas',
        db_column='documento_id'
    )
    periodo = models.CharField(
        max_length=20,
        choices=PERIODO_CHOICES
    )
    fecha_inicio = models.DateField()
    total_visitas = models.PositiveIntegerField(default=0)
    total_descargas = models.PositiveIntegerField(default=0)
    visitas_unicas = models.PositiveIntegerField(default=0)
    descargas_unicas = models.PositiveIntegerField(default=0)
    tiempo_promedio_lectura = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='En segundos'
    )
    
    class Meta:
        db_table = 'estadisticas_agregadas'
        verbose_name = 'Estadística Agregada'
        verbose_name_plural = 'Estadísticas Agregadas'
        unique_together = [['documento', 'periodo', 'fecha_inicio']]
        ordering = ['documento', '-fecha_inicio']
        indexes = [
            models.Index(fields=['documento'], name='idx_estad_agr_doc'),
            models.Index(fields=['fecha_inicio'], name='idx_estad_agr_fecha'),
        ]
    
    def __str__(self):
        return f"{self.documento} - {self.get_periodo_display()} ({self.fecha_inicio})"
