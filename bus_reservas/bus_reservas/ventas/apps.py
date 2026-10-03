"""
Configuración de la aplicación VENTAS.
"""

from django.apps import AppConfig


class VentasConfig(AppConfig):
    """Configura la aplicaci?n de ventas y gesti?n de ?rdenes."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ventas'
    verbose_name = 'Gestión de Ventas y Órdenes'