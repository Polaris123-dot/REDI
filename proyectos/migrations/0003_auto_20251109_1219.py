# Generated manually

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def eliminar_autores_sin_usuario(apps, schema_editor):
    """Elimina los autores que no tienen usuario asignado"""
    ProyectoAutor = apps.get_model('proyectos', 'ProyectoAutor')
    # Eliminar todos los autores que tengan usuario NULL
    ProyectoAutor.objects.filter(usuario__isnull=True).delete()


def reverse_eliminar_autores_sin_usuario(apps, schema_editor):
    """Función reversa - no se puede recuperar datos eliminados"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('proyectos', '0002_proyectoautor'),
    ]

    operations = [
        # Primero eliminar autores sin usuario
        migrations.RunPython(
            eliminar_autores_sin_usuario,
            reverse_eliminar_autores_sin_usuario
        ),
        # Hacer el campo usuario obligatorio
        migrations.AlterField(
            model_name='proyectoautor',
            name='usuario',
            field=models.ForeignKey(
                db_column='usuario_id',
                help_text='Usuario del sistema (obligatorio)',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='autoria_proyectos',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        # Eliminar campos nombre, apellidos, email (ya no se usan)
        migrations.RemoveField(
            model_name='proyectoautor',
            name='nombre',
        ),
        migrations.RemoveField(
            model_name='proyectoautor',
            name='apellidos',
        ),
        migrations.RemoveField(
            model_name='proyectoautor',
            name='email',
        ),
        # Agregar constraint unique_together
        migrations.AlterUniqueTogether(
            name='proyectoautor',
            unique_together={('proyecto', 'usuario')},
        ),
    ]
