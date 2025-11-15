from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Persona


class PersonaInline(admin.StackedInline):
    """Inline admin para Persona en el admin de User"""
    model = Persona
    can_delete = False
    verbose_name_plural = 'Información Adicional'
    fields = (
        'telefono',
        'institucion',
        'departamento',
        'cargo',
        'biografia',
        'foto_perfil',
        'orcid_id',
        'google_scholar_id',
        'researchgate_id',
        'linkedin_url',
        'email_verificado',
        'ultimo_acceso',
        'preferencias_notificaciones',
    )


class UserAdmin(BaseUserAdmin):
    """Extiende el UserAdmin de Django para incluir Persona"""
    inlines = (PersonaInline,)


# Re-registrar UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Persona)
class PersonaAdmin(admin.ModelAdmin):
    """Admin para el modelo Persona"""
    list_display = ('user', 'institucion', 'departamento', 'orcid_id', 'email_verificado')
    list_filter = ('email_verificado', 'institucion', 'departamento')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 
                     'institucion', 'orcid_id', 'google_scholar_id')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion', 'ultimo_acceso')
    
    fieldsets = (
        ('Usuario', {
            'fields': ('user',)
        }),
        ('Información Personal', {
            'fields': ('telefono', 'biografia', 'foto_perfil')
        }),
        ('Información Institucional', {
            'fields': ('institucion', 'departamento', 'cargo')
        }),
        ('Identificadores Académicos', {
            'fields': ('orcid_id', 'google_scholar_id', 'researchgate_id', 'linkedin_url')
        }),
        ('Estado y Preferencias', {
            'fields': ('email_verificado', 'ultimo_acceso', 'preferencias_notificaciones')
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
