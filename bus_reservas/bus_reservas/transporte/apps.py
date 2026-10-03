"""
Configuración de la aplicación TRANSPORTE.
"""

from django.apps import AppConfig


class TransporteConfig(AppConfig):
    """Configura la aplicaci?n de transporte con nombres legibles para admin."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'transporte'
    verbose_name = 'Gestión de Transporte'