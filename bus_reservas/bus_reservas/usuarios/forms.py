"""Formularios del portal web para registrar pasajeros y mantener el flujo de login."""
from django.contrib.auth.models import Group
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario


class RegistroUsuarioForm(UserCreationForm):
    """Creates a passenger account for the template-based web interface."""

    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ('username', 'first_name', 'last_name', 'email')

    def save(self, commit=True):
        """Crea el usuario y lo asocia al grupo de pasajeros del portal web."""
        usuario = super().save(commit=False)
        usuario.rol = Usuario.Rol.PASAJERO
        if commit:
            usuario.save()
            pasajero_group, _ = Group.objects.get_or_create(name='PASAJERO')
            usuario.groups.add(pasajero_group)
        return usuario
