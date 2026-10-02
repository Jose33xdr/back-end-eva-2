"""
Configuración de la aplicación TRANSPORTE.
"""

from django.apps import AppConfig


class TransporteConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'transporte'
    verbose_name = 'Gestión de Transporte'