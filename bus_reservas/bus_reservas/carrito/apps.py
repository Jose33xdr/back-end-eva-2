"""
Configuración de la aplicación CARRITO.
"""

from django.apps import AppConfig


class CarritoConfig(AppConfig):
    """Configura la aplicaci?n del carrito y sus modelos de compra."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'carrito'
    verbose_name = 'Carrito de Pasajes'