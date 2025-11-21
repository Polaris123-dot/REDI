from django import forms
from django.contrib.auth.models import User
from .models import Persona

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
    class Meta:
        model = Persona
        fields = [
            'telefono', 'institucion', 'departamento', 'cargo', 
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
        }
