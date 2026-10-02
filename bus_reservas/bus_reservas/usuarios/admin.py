"""
Admin de la aplicación USUARIOS.

Registra el modelo Usuario en el panel de administración de Django.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """
    Configuración del admin para el modelo Usuario personalizado.
    """
    list_display = ['username', 'email', 'first_name', 'last_name', 'get_rol', 'is_active', 'date_joined']
    list_filter = ['is_active', 'is_staff', 'is_superuser', 'groups']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Información adicional', {'fields': ('rol',)}),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información adicional', {'fields': ('rol', 'email', 'first_name', 'last_name')}),
    )
    
    def get_rol(self, obj):
        return obj.get_rol()
    get_rol.short_description = 'Rol'