from django.db import models
from django.contrib.auth.models import User
from repositorio.models import Documento


class IndiceBusqueda(models.Model):
    """
    Índice de búsqueda full-text para documentos.
    """
    documento = models.OneToOneField(
        Documento,
        on_delete=models.CASCADE,
        related_name='indice_busqueda',
        db_column='documento_id'
    )
    contenido_indexado = models.TextField()
    palabras_clave_indexadas = models.TextField(null=True, blank=True)
    fecha_indexacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'indices_busqueda'
        verbose_name = 'Índice de Búsqueda'
        verbose_name_plural = 'Índices de Búsqueda'
    
    def __str__(self):
        return f"Índice: {self.documento.titulo}"


class Busqueda(models.Model):
    """
    Registro de búsquedas realizadas.
    """
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='busquedas',
        db_column='usuario_id'
    )
    termino_busqueda = models.CharField(max_length=500)
    filtros_aplicados = models.JSONField(null=True, blank=True)
    resultados_encontrados = models.PositiveIntegerField(default=0)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'busquedas'
        verbose_name = 'Búsqueda'
        verbose_name_plural = 'Búsquedas'
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['usuario'], name='idx_busquedas_usuario'),
            models.Index(fields=['fecha'], name='idx_busquedas_fecha'),
        ]
    
    def __str__(self):
        return f"{self.termino_busqueda} - {self.fecha}"
