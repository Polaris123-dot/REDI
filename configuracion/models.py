from django.db import models
from django.contrib.auth.models import User


class ConfiguracionSistema(models.Model):
    """
    Configuración del sistema.
    """
    TIPO_CHOICES = [
        ('texto', 'Texto'),
        ('numero', 'Número'),
        ('booleano', 'Booleano'),
        ('json', 'JSON'),
        ('fecha', 'Fecha'),
    ]
    
    clave = models.CharField(max_length=255, unique=True)
    valor = models.TextField(null=True, blank=True)
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default='texto'
    )
    categoria = models.CharField(max_length=100, null=True, blank=True)
    descripcion = models.TextField(null=True, blank=True)
    es_editable = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'configuracion_sistema'
        verbose_name = 'Configuración del Sistema'
        verbose_name_plural = 'Configuraciones del Sistema'
        ordering = ['categoria', 'clave']
        indexes = [
            models.Index(fields=['clave'], name='idx_config_clave'),
            models.Index(fields=['categoria'], name='idx_config_categoria'),
        ]
    
    def __str__(self):
        return f"{self.clave} = {self.valor}"


class LogSistema(models.Model):
    """
    Logs del sistema.
    """
    NIVEL_CHOICES = [
        ('DEBUG', 'DEBUG'),
        ('INFO', 'INFO'),
        ('WARNING', 'WARNING'),
        ('ERROR', 'ERROR'),
        ('CRITICAL', 'CRITICAL'),
    ]
    
    nivel = models.CharField(
        max_length=10,
        choices=NIVEL_CHOICES
    )
    modulo = models.CharField(max_length=100, null=True, blank=True)
    mensaje = models.TextField()
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs_sistema',
        db_column='usuario_id'
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    datos_adicionales = models.JSONField(null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'logs_sistema'
        verbose_name = 'Log del Sistema'
        verbose_name_plural = 'Logs del Sistema'
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['nivel'], name='idx_logs_nivel'),
            models.Index(fields=['modulo'], name='idx_logs_modulo'),
            models.Index(fields=['usuario'], name='idx_logs_usuario'),
            models.Index(fields=['fecha'], name='idx_logs_fecha'),
        ]
    
    def __str__(self):
        return f"{self.nivel} - {self.modulo} - {self.fecha}"
