from django.db import models
from django.contrib.auth.models import User
from repositorio.models import Documento


class Comentario(models.Model):
    """
    Comentarios sobre documentos.
    Permite estructura jerárquica mediante comentario_padre.
    """
    documento = models.ForeignKey(
        Documento,
        on_delete=models.CASCADE,
        related_name='comentarios',
        db_column='documento_id'
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comentarios',
        db_column='usuario_id'
    )
    comentario_padre = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='respuestas',
        db_column='comentario_padre_id'
    )
    contenido = models.TextField()
    es_moderado = models.BooleanField(default=False)
    es_publico = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'comentarios'
        verbose_name = 'Comentario'
        verbose_name_plural = 'Comentarios'
        ordering = ['documento', '-fecha_creacion']
        indexes = [
            models.Index(fields=['documento'], name='idx_comentarios_documento'),
            models.Index(fields=['usuario'], name='idx_comentarios_usuario'),
            models.Index(fields=['comentario_padre'], name='idx_comentarios_padre'),
        ]
    
    def __str__(self):
        return f"{self.documento} - {self.usuario.username} - {self.fecha_creacion}"


class Valoracion(models.Model):
    """
    Valoraciones/calificaciones de documentos.
    """
    documento = models.ForeignKey(
        Documento,
        on_delete=models.CASCADE,
        related_name='valoraciones',
        db_column='documento_id'
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='valoraciones',
        db_column='usuario_id'
    )
    calificacion = models.PositiveIntegerField(help_text='Calificación del 1 al 5')
    comentario = models.TextField(null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'valoraciones'
        verbose_name = 'Valoración'
        verbose_name_plural = 'Valoraciones'
        unique_together = [['documento', 'usuario']]
        ordering = ['documento', '-fecha']
        indexes = [
            models.Index(fields=['documento'], name='idx_valoraciones_documento'),
            models.Index(fields=['usuario'], name='idx_valoraciones_usuario'),
        ]
    
    def __str__(self):
        return f"{self.documento} - {self.usuario.username} - {self.calificacion}/5"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.calificacion < 1 or self.calificacion > 5:
            raise ValidationError('La calificación debe estar entre 1 y 5')


class Cita(models.Model):
    """
    Citas entre documentos.
    """
    documento_citado = models.ForeignKey(
        Documento,
        on_delete=models.CASCADE,
        related_name='citas_recibidas',
        db_column='documento_citado_id'
    )
    documento_que_cita = models.ForeignKey(
        Documento,
        on_delete=models.CASCADE,
        related_name='citas_realizadas',
        db_column='documento_que_cita_id'
    )
    contexto = models.TextField(null=True, blank=True)
    fecha_citacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'citas'
        verbose_name = 'Cita'
        verbose_name_plural = 'Citas'
        unique_together = [['documento_citado', 'documento_que_cita']]
        ordering = ['documento_citado', '-fecha_citacion']
        indexes = [
            models.Index(fields=['documento_citado'], name='idx_citado'),
            models.Index(fields=['documento_que_cita'], name='idx_que_cita'),
        ]
    
    def __str__(self):
        return f"{self.documento_que_cita} cita a {self.documento_citado}"


class ReferenciaBibliografica(models.Model):
    """
    Referencias bibliográficas de documentos.
    """
    TIPO_CHOICES = [
        ('articulo', 'Artículo'),
        ('libro', 'Libro'),
        ('capitulo', 'Capítulo'),
        ('tesis', 'Tesis'),
        ('congreso', 'Congreso'),
        ('patente', 'Patente'),
        ('web', 'Web'),
        ('otros', 'Otros'),
    ]
    
    documento = models.ForeignKey(
        Documento,
        on_delete=models.CASCADE,
        related_name='referencias_bibliograficas',
        db_column='documento_id'
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default='otros'
    )
    titulo = models.CharField(max_length=500)
    autores = models.TextField(null=True, blank=True)
    año = models.PositiveIntegerField(null=True, blank=True)
    doi = models.CharField(max_length=255, null=True, blank=True)
    url = models.URLField(max_length=1000, null=True, blank=True)
    cita_completa = models.TextField(null=True, blank=True)
    orden = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'referencias_bibliograficas'
        verbose_name = 'Referencia Bibliográfica'
        verbose_name_plural = 'Referencias Bibliográficas'
        ordering = ['documento', 'orden']
        indexes = [
            models.Index(fields=['documento'], name='idx_referencias_documento'),
        ]
    
    def __str__(self):
        return f"{self.documento} - {self.titulo}"
