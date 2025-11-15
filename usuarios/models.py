from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator


class Persona(models.Model):
    """
    Modelo que extiende el User de Django con información adicional
    relacionada con el repositorio digital de investigación.
    """
    # Relación uno a uno con el User de Django
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='persona',
        verbose_name='Usuario',
        help_text='Usuario de Django asociado a esta persona'
    )
    
    # Información personal adicional
    telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="El teléfono debe estar en formato: '+999999999'. Hasta 15 dígitos permitidos."
            )
        ],
        verbose_name='Teléfono',
        help_text='Número de teléfono de contacto'
    )
    
    # Información institucional
    institucion = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Institución',
        help_text='Institución a la que pertenece'
    )
    
    departamento = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Departamento',
        help_text='Departamento o unidad académica'
    )
    
    cargo = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Cargo',
        help_text='Cargo o posición actual'
    )
    
    # Biografía y perfil
    biografia = models.TextField(
        blank=True,
        null=True,
        verbose_name='Biografía',
        help_text='Biografía o descripción del perfil'
    )
    
    foto_perfil = models.ImageField(
        upload_to='fotos_perfil/',
        blank=True,
        null=True,
        verbose_name='Foto de Perfil',
        help_text='Foto de perfil del usuario'
    )
    
    # Identificadores académicos
    orcid_id = models.CharField(
        max_length=19,
        blank=True,
        null=True,
        unique=True,
        verbose_name='ORCID ID',
        help_text='Identificador ORCID (formato: 0000-0000-0000-0000)',
        validators=[
            RegexValidator(
                regex=r'^\d{4}-\d{4}-\d{4}-\d{4}$',
                message="El ORCID debe estar en formato: 0000-0000-0000-0000"
            )
        ]
    )
    
    google_scholar_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Google Scholar ID',
        help_text='ID de Google Scholar'
    )
    
    researchgate_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='ResearchGate ID',
        help_text='ID de ResearchGate'
    )
    
    linkedin_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='LinkedIn URL',
        help_text='URL del perfil de LinkedIn'
    )
    
    # Estado y preferencias
    email_verificado = models.BooleanField(
        default=False,
        verbose_name='Email Verificado',
        help_text='Indica si el email ha sido verificado'
    )
    
    ultimo_acceso = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Último Acceso',
        help_text='Fecha y hora del último acceso al sistema'
    )
    
    preferencias_notificaciones = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Preferencias de Notificaciones',
        help_text='Preferencias de notificaciones en formato JSON'
    )
    
    # Campos de auditoría
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )
    
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Fecha de Actualización'
    )
    
    class Meta:
        verbose_name = 'Persona'
        verbose_name_plural = 'Personas'
        ordering = ['user__last_name', 'user__first_name']
        indexes = [
            models.Index(fields=['orcid_id'], name='idx_persona_orcid'),
            models.Index(fields=['institucion'], name='idx_persona_institucion'),
            models.Index(fields=['user'], name='idx_persona_user'),
        ]
    
    def __str__(self):
        if self.user.get_full_name():
            return f"{self.user.get_full_name()} ({self.user.username})"
        return f"{self.user.username}"
    
    def get_nombre_completo(self):
        """Retorna el nombre completo de la persona"""
        return self.user.get_full_name() or self.user.username
    
    def get_orcid_url(self):
        """Retorna la URL del perfil ORCID si existe"""
        if self.orcid_id:
            return f"https://orcid.org/{self.orcid_id}"
        return None
    
    def get_google_scholar_url(self):
        """Retorna la URL del perfil de Google Scholar si existe"""
        if self.google_scholar_id:
            return f"https://scholar.google.com/citations?user={self.google_scholar_id}"
        return None
    
    def get_researchgate_url(self):
        """Retorna la URL del perfil de ResearchGate si existe"""
        if self.researchgate_id:
            return f"https://www.researchgate.net/profile/{self.researchgate_id}"
        return None
