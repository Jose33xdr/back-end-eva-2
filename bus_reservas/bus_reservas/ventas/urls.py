"""
URLs de la aplicación VENTAS.

Endpoints para checkout, órdenes y cambio de estados.
"""

from django.urls import path
from .views import (
    MisOrdenesView, MisBoletosView, OrdenDetalleView,
    checkout, cambiar_estado_orden, AdminOrdenesView
)

urlpatterns = [
    # Mis reservas (pasajero autenticado)
    path('mis-reservas/', MisOrdenesView.as_view(), name='mis-reservas'),
    path('mis-boletos/', MisBoletosView.as_view(), name='mis-boletos'),
    
    # Checkout - crear orden desde carrito
    path('checkout/', checkout, name='checkout'),
    
    # Listado de todas las órdenes (admin)
    path('', AdminOrdenesView.as_view(), name='ordenes-lista'),
    
    # Detalle de orden
    path('<int:pk>/', OrdenDetalleView.as_view(), name='orden-detalle'),
    
    # Cambio de estado (admin)
    path('<int:orden_id>/estado/', cambiar_estado_orden, name='orden-cambiar-estado'),
]