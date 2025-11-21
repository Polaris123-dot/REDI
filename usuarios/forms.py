from django import forms
from django.contrib.auth.models import User
from .models import Persona

<<<<<<< Updated upstream
<<<<<<< Updated upstream
class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(label='Correo Electrónico', widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(label='Nombre', widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label='Apellidos', widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        }
        help_texts = {
            'username': 'El nombre de usuario no se puede cambiar.',
        }

class PersonaUpdateForm(forms.ModelForm):
=======
=======
>>>>>>> Stashed changes
class UserForm(forms.ModelForm):
    """Formulario para editar datos básicos del usuario"""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellidos'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Correo electrónico'}),
        }
        labels = {
            'first_name': 'Nombre',
            'last_name': 'Apellidos',
            'email': 'Correo electrónico',
        }

class PersonaForm(forms.ModelForm):
    """Formulario para editar datos extendidos del perfil"""
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    class Meta:
        model = Persona
        fields = [
            'telefono', 'institucion', 'departamento', 'cargo', 
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            'biografia', 'foto_perfil', 
            'orcid_id', 'google_scholar_id', 'researchgate_id', 'linkedin_url'
        ]
        widgets = {
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+51 999 999 999'}),
            'institucion': forms.TextInput(attrs={'class': 'form-control'}),
            'departamento': forms.TextInput(attrs={'class': 'form-control'}),
            'cargo': forms.TextInput(attrs={'class': 'form-control'}),
            'biografia': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'foto_perfil': forms.FileInput(attrs={'class': 'custom-file-input'}),
            'orcid_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0000-0000-0000-0000'}),
            'google_scholar_id': forms.TextInput(attrs={'class': 'form-control'}),
            'researchgate_id': forms.TextInput(attrs={'class': 'form-control'}),
            'linkedin_url': forms.URLInput(attrs={'class': 'form-control'}),
=======
=======
>>>>>>> Stashed changes
            'biografia', 'foto_perfil', 'orcid_id', 
            'google_scholar_id', 'researchgate_id', 'linkedin_url',
            'preferencias_notificaciones'
        ]
        widgets = {
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+53 55555555'}),
            'institucion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la institución'}),
            'departamento': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Departamento o área'}),
            'cargo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cargo actual'}),
            'biografia': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Breve biografía profesional'}),
            'foto_perfil': forms.FileInput(attrs={'class': 'form-control-file'}),
            'orcid_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0000-0000-0000-0000'}),
            'google_scholar_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ID de Google Scholar'}),
            'researchgate_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ID de ResearchGate'}),
            'linkedin_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://linkedin.com/in/usuario'}),
            'preferencias_notificaciones': forms.HiddenInput(), # Se manejará por separado si es necesario
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        }
