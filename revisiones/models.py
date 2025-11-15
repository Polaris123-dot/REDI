from django.db import models
from django.contrib.auth.models import User
from repositorio.models import Documento


class CriterioRevision(models.Model):
    """
    Criterios de revisión reutilizables.
    """
    TIPO_CHOICES = [
        ('numerico', 'Numérico'),
        ('texto', 'Texto'),
        ('booleano', 'Booleano'),
        ('opcion', 'Opción'),
    ]
    
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(null=True, blank=True)
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default='numerico'
    )
    escala_minima = models.PositiveIntegerField(null=True, blank=True)
    escala_maxima = models.PositiveIntegerField(null=True, blank=True)
    opciones = models.JSONField(null=True, blank=True, help_text='Opciones para tipo opcion')
    es_obligatorio = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'criterios_revision'
        verbose_name = 'Criterio de Revisión'
        verbose_name_plural = 'Criterios de Revisión'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre


class ProcesoRevision(models.Model):
    """
    Proceso de revisión de un documento.
    """
    TIPO_REVISION_CHOICES = [
        ('peer_review', 'Peer Review'),
        ('editorial', 'Editorial'),
        ('administrativa', 'Administrativa'),
    ]
    
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_revision', 'En Revisión'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
        ('requiere_cambios', 'Requiere Cambios'),
    ]
    
    documento = models.ForeignKey(
        Documento,
        on_delete=models.CASCADE,
        related_name='procesos_revision',
        db_column='documento_id'
    )
    tipo_revision = models.CharField(
        max_length=20,
        choices=TIPO_REVISION_CHOICES
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='pendiente'
    )
    iniciado_por = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        related_name='procesos_revision_iniciados',
        db_column='iniciado_por'
    )
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_finalizacion = models.DateTimeField(null=True, blank=True)
    notas_generales = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'procesos_revision'
        verbose_name = 'Proceso de Revisión'
        verbose_name_plural = 'Procesos de Revisión'
        ordering = ['-fecha_inicio']
        indexes = [
            models.Index(fields=['documento'], name='idx_proc_rev_doc'),
            models.Index(fields=['estado'], name='idx_proc_rev_estado'),
        ]
    
    def __str__(self):
        return f"{self.documento} - {self.get_tipo_revision_display()} ({self.get_estado_display()})"


class Revision(models.Model):
    """
    Revisión individual dentro de un proceso de revisión.
    """
    ESTADO_CHOICES = [
        ('asignado', 'Asignado'),
        ('en_progreso', 'En Progreso'),
        ('completado', 'Completado'),
        ('rechazado', 'Rechazado'),
    ]
    
    RECOMENDACION_CHOICES = [
        ('aprobar', 'Aprobar'),
        ('aprobar_con_cambios', 'Aprobar con Cambios'),
        ('rechazar', 'Rechazar'),
        ('requiere_revision', 'Requiere Revisión'),
    ]
    
    proceso_revision = models.ForeignKey(
        ProcesoRevision,
        on_delete=models.CASCADE,
        related_name='revisiones',
        db_column='proceso_revision_id'
    )
    revisor = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        related_name='revisiones_asignadas',
        db_column='revisor_id'
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='asignado'
    )
    calificacion_general = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Calificación del 1 al 5'
    )
    comentarios_publicos = models.TextField(null=True, blank=True)
    comentarios_privados = models.TextField(null=True, blank=True)
    recomendacion = models.CharField(
        max_length=30,
        choices=RECOMENDACION_CHOICES,
        null=True,
        blank=True
    )
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    fecha_completacion = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'revisiones'
        verbose_name = 'Revisión'
        verbose_name_plural = 'Revisiones'
        ordering = ['proceso_revision', '-fecha_asignacion']
        indexes = [
            models.Index(fields=['proceso_revision'], name='idx_revisiones_proceso'),
            models.Index(fields=['revisor'], name='idx_revisiones_revisor'),
        ]
    
    def __str__(self):
        return f"{self.proceso_revision} - {self.revisor.get_full_name()}"


class EvaluacionCriterio(models.Model):
    """
    Evaluación de un criterio específico dentro de una revisión.
    """
    revision = models.ForeignKey(
        Revision,
        on_delete=models.CASCADE,
        related_name='evaluaciones_criterios',
        db_column='revision_id'
    )
    criterio = models.ForeignKey(
        CriterioRevision,
        on_delete=models.CASCADE,
        related_name='evaluaciones',
        db_column='criterio_id'
    )
    valor_numerico = models.PositiveIntegerField(null=True, blank=True)
    valor_texto = models.TextField(null=True, blank=True)
    valor_booleano = models.BooleanField(null=True, blank=True)
    valor_opcion = models.CharField(max_length=255, null=True, blank=True)
    comentarios = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'evaluaciones_criterios'
        verbose_name = 'Evaluación de Criterio'
        verbose_name_plural = 'Evaluaciones de Criterios'
        unique_together = [['revision', 'criterio']]
        indexes = [
            models.Index(fields=['revision'], name='idx_evaluaciones_revision'),
            models.Index(fields=['criterio'], name='idx_evaluaciones_criterio'),
        ]
    
    def __str__(self):
        return f"{self.revision} - {self.criterio.nombre}"
