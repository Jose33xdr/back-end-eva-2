"""
Configuración de la aplicación USUARIOS.
"""

from django.apps import AppConfig


class UsuariosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'usuarios'
    verbose_name = 'Gestión de Usuarios'
    
    def ready(self):
        # Importar signals para crear grupos por defecto
        import usuarios.signals  # noqa