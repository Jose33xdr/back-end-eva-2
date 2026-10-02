"""
Modelos de la aplicación USUARIOS.

Esta aplicación extiende el modelo de usuario de Django para agregar
funcionalidad de roles mediante grupos de Django.
Roles disponibles: PASAJERO, ADMINISTRADOR
"""

from django.contrib.auth.models import AbstractUser, Group
from django.db import models


class Usuario(AbstractUser):
    """
    Modelo de usuario personalizado que extiende AbstractUser.
    
    Utiliza grupos de Django para definir roles:
    - PASAJERO: Usuario normal que puede comprar pasajes
    - ADMINISTRADOR: Usuario con permisos de gestión completa
    
    Los claims del JWT incluyen: username, user_id, rol
    """
    
    class Rol(models.TextChoices):
        PASAJERO = 'PASAJERO', 'Pasajero'
        ADMINISTRADOR = 'ADMINISTRADOR', 'Administrador'
    
    # Campo opcional para rol directo (alternativa a grupos)
    # Se mantiene para compatibilidad, pero se usan grupos principalmente
    rol = models.CharField(
        max_length=20,
        choices=Rol.choices,
        default=Rol.PASAJERO,
        verbose_name='Rol del usuario',
        help_text='Rol del usuario en el sistema'
    )
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        db_table = 'usuarios_usuario'
    
    def __str__(self):
        return self.username
    
    def get_rol(self):
        """
        Obtiene el rol del usuario basado en sus grupos.
        Prioriza grupos de Django sobre el campo rol.
        """
        if self.groups.filter(name='ADMINISTRADOR').exists():
            return self.Rol.ADMINISTRADOR
        elif self.groups.filter(name='PASAJERO').exists():
            return self.Rol.PASAJERO
        return self.rol
    
    def is_admin(self):
        """Verifica si el usuario es administrador."""
        return self.get_rol() == self.Rol.ADMINISTRADOR or self.is_superuser
    
    def is_pasajero(self):
        """Verifica si el usuario es pasajero."""
        return self.get_rol() == self.Rol.PASAJERO


# Crear grupos por defecto al migrar
def crear_grupos_por_defecto(sender, **kwargs):
    """
    Crea los grupos PASAJERO y ADMINISTRADOR si no existen.
    Se ejecuta automáticamente después de las migraciones.
    """
    Group.objects.get_or_create(name='PASAJERO')
    Group.objects.get_or_create(name='ADMINISTRADOR')