"""
Signals de la aplicación USUARIOS.

Crea los grupos de roles (PASAJERO, ADMINISTRADOR) automáticamente
después de ejecutar las migraciones.
"""

from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import Group


@receiver(post_migrate)
def crear_grupos_roles(sender, **kwargs):
    """
    Crea los grupos de roles si no existen.
    Se ejecuta después de cada migración.
    """
    if sender.name == 'usuarios':
        Group.objects.get_or_create(name='PASAJERO')
        Group.objects.get_or_create(name='ADMINISTRADOR')