"""
Modelos de la aplicación CARRITO.

Define el carrito de pasajes y sus items.
El carrito tiene relación OneToOne con Usuario y persiste después del logout.
"""

from django.db import models
from django.conf import settings
from transporte.models import Asiento


class Carro(models.Model):
    """
    Modelo para el carrito de pasajes del usuario.
    
    Relación OneToOne con Usuario - cada usuario tiene un solo carrito.
    El carrito permanece guardado aunque el usuario cierre sesión (logout).
    
    Campos:
    - usuario: Usuario dueño del carrito
    - activo: Indica si el carrito está activo
    - fecha_creacion: Cuándo se creó el carrito
    """
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='carro',
        verbose_name='Usuario'
    )
    activo = models.BooleanField(
        default=True,
        verbose_name='Activo'
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )
    
    class Meta:
        verbose_name = 'Carro'
        verbose_name_plural = 'Carros'
        db_table = 'carrito_carro'
    
    def __str__(self):
        return f'Carro de {self.usuario.username}'
    
    @property
    def total_items(self):
        """Retorna el total de items en el carrito."""
        return self.items.count()
    
    @property
    def total_precio(self):
        """Calcula el precio total de los items en el carrito."""
        return sum(item.subtotal for item in self.items.all())


class ItemCarro(models.Model):
    """
    Modelo para items del carrito.
    
    Cada item representa un asiento seleccionado en un servicio.
    Relación: ForeignKey a Carro y ForeignKey a Asiento.
    
    Se evita productos repetidos: un mismo asiento no puede estar dos veces
    en el mismo carrito (constraint unique_together).
    """
    carro = models.ForeignKey(
        Carro,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Carro'
    )
    asiento = models.ForeignKey(
        Asiento,
        on_delete=models.CASCADE,
        related_name='items_carro',
        verbose_name='Asiento'
    )
    cantidad = models.PositiveIntegerField(
        default=1,
        verbose_name='Cantidad'
    )
    nombre_pasajero = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='Nombre completo del ocupante'
    )
    documento_pasajero = models.CharField(
        max_length=32,
        blank=True,
        null=True,
        verbose_name='RUT o pasaporte del ocupante'
    )
    fecha_agregado = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha agregado'
    )
    
    class Meta:
        verbose_name = 'Item Carro'
        verbose_name_plural = 'Items Carro'
        db_table = 'carrito_itemcarro'
        # Evitar asientos repetidos en el mismo carro
        constraints = [
            models.UniqueConstraint(
                fields=['carro', 'asiento'],
                name='unique_itemcarro_carro_asiento'
            )
        ]
    
    def __str__(self):
        return f'{self.carro} - Asiento {self.asiento.numero} ({self.asiento.servicio})'
    
    @property
    def subtotal(self):
        """Calcula el subtotal (precio del servicio * cantidad)."""
        return self.asiento.precio * self.cantidad