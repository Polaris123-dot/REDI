from django.db import models
from django.contrib.auth.models import User
from repositorio.models import Documento


class TipoNotificacion(models.Model):
    """
    Tipos de notificaciones del sistema.
    """
    codigo = models.CharField(max_length=100, unique=True)
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(null=True, blank=True)
    plantilla = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'tipos_notificacion'
        verbose_name = 'Tipo de Notificación'
        verbose_name_plural = 'Tipos de Notificación'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre


class Notificacion(models.Model):
    """
    Notificaciones para usuarios.
    """
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notificaciones',
        db_column='usuario_id'
    )
    tipo_notificacion = models.ForeignKey(
        TipoNotificacion,
        on_delete=models.RESTRICT,
        related_name='notificaciones',
        db_column='tipo_notificacion_id'
    )
    titulo = models.CharField(max_length=500)
    mensaje = models.TextField()
    url_relacionada = models.CharField(max_length=1000, null=True, blank=True)
    documento = models.ForeignKey(
        Documento,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notificaciones',
        db_column='documento_id'
    )
    es_leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notificaciones'
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['usuario'], name='idx_notificaciones_usuario'),
            models.Index(fields=['tipo_notificacion'], name='idx_notificaciones_tipo'),
            models.Index(fields=['es_leida'], name='idx_notificaciones_leida'),
            models.Index(fields=['fecha_creacion'], name='idx_notificaciones_fecha'),
        ]
    
    def __str__(self):
        return f"{self.usuario.username} - {self.titulo}"
