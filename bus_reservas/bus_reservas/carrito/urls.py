"""
URLs de la aplicación CARRITO.

Endpoints para gestión del carrito de pasajes.
"""

from django.urls import path
from .views import CarroView, agregar_al_carro, quitar_del_carro, limpiar_carro

urlpatterns = [
    # Ver carrito del usuario autenticado
    path('', CarroView.as_view(), name='carro-detalle'),
    
    # Agregar asiento al carrito
    path('agregar/', agregar_al_carro, name='carro-agregar'),
    
    # Quitar item del carrito
    path('quitar/<int:item_id>/', quitar_del_carro, name='carro-quitar'),
    
    # Vaciar carrito completo
    path('limpiar/', limpiar_carro, name='carro-limpiar'),
]