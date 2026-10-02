"""
Permisos personalizados de la aplicación USUARIOS.

Define clases de permisos basadas en roles (grupos de Django):
- Publico: Acceso sin autenticación
- EsPasajero: Usuario autenticado con rol PASAJERO
- EsAdmin: Usuario autenticado con rol ADMINISTRADOR
"""

from rest_framework import permissions
from django.contrib.auth import get_user_model

Usuario = get_user_model()


class Publico(permissions.BasePermission):
    """
    Permiso para acceso público.
    
    Permite acceso a cualquiera (autenticado o no).
    Se usa para endpoints de consulta pública como listar servicios, rutas, ciudades.
    """
    
    def has_permission(self, request, view):
        return True


class EsPasajero(permissions.BasePermission):
    """
    Permiso para usuarios con rol PASAJERO.
    
    Requiere:
    - Usuario autenticado
    - Rol PASAJERO (via grupo Django)
    
    Se usa para: carrito, checkout, mis reservas
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superusuarios tienen acceso a todo
        if request.user.is_superuser:
            return True
        
        # Verificar rol via grupos
        return request.user.groups.filter(name='PASAJERO').exists() or \
               request.user.rol == Usuario.Rol.PASAJERO


class EsAdmin(permissions.BasePermission):
    """
    Permiso para usuarios con rol ADMINISTRADOR.
    
    Requiere:
    - Usuario autenticado
    - Rol ADMINISTRADOR (via grupo Django) o is_superuser
    
    Se usa para: CRUD de transporte, gestión de órdenes, cambio de estados
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superusuarios tienen acceso a todo
        if request.user.is_superuser:
            return True
        
        # Verificar rol via grupos
        return request.user.groups.filter(name='ADMINISTRADOR').exists() or \
               request.user.rol == Usuario.Rol.ADMINISTRADOR


class EsPropietarioOAdmin(permissions.BasePermission):
    """
    Permiso para propietario del objeto o administrador.
    
    Se usa para: ver/modificar propia orden, perfil propio
    """
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin puede acceder a todo
        if request.user.is_superuser or request.user.is_admin():
            return True
        
        # Verificar si es el propietario
        # Asumimos que el objeto tiene campo 'usuario' o es el propio usuario
        if hasattr(obj, 'usuario'):
            return obj.usuario == request.user
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return obj == request.user