"""
Modelos de la aplicación VENTAS.

Define las órdenes de compra y sus items.
Implementa control de estados y precios históricos congelados.
"""

from django.db import models
from django.conf import settings
import uuid
from transporte.models import Servicio, Asiento


class Orden(models.Model):
    """
    Modelo para órdenes de compra (reservas).
    
    Estados:
    - PENDIENTE: Orden creada, esperando pago
    - PAGADO: Pago confirmado, asientos marcados como ocupados
    - ENTREGADO: Pasaje entregado/usado
    - CANCELADO: Orden cancelada, asientos liberados
    
    El stock (asientos) NO se descuenta al crear la orden (PENDIENTE).
    Solo se descuenta al cambiar a PAGADO.
    Si se cancela desde PAGADO, se libera el asiento.
    """
    
    class Estado(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        PAGADO = 'PAGADO', 'Pagado'
        ENTREGADO = 'ENTREGADO', 'Entregado'
        CANCELADO = 'CANCELADO', 'Cancelado'
    
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ordenes',
        verbose_name='Usuario'
    )
    fecha = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de la orden'
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Total'
    )
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
        verbose_name='Estado'
    )
    
    class Meta:
        verbose_name = 'Orden'
        verbose_name_plural = 'Órdenes'
        ordering = ['-fecha']
        db_table = 'ventas_orden'
    
    def __str__(self):
        return f'Orden #{self.id} - {self.usuario.username} - {self.get_estado_display()}'
    
    def calcular_total(self):
        """Calcula el total sumando los items."""
        return sum(item.subtotal for item in self.items.all())


class ItemOrden(models.Model):
    """
    Modelo para items de una orden.
    
    Congela el precio al momento de la compra (precio_unitario).
    Si luego cambia el precio del servicio, la orden mantiene el valor original.
    
    Relaciones:
    - orden: ForeignKey a Orden
    - servicio: ForeignKey a Servicio (para referencia)
    - asiento: ForeignKey a Asiento (el asiento específico comprado)
    - precio_unitario: Precio congelado al momento de la compra
    """
    orden = models.ForeignKey(
        Orden,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Orden'
    )
    servicio = models.ForeignKey(
        Servicio,
        on_delete=models.PROTECT,
        related_name='items_orden',
        verbose_name='Servicio'
    )
    asiento = models.ForeignKey(
        Asiento,
        on_delete=models.PROTECT,
        related_name='items_orden',
        verbose_name='Asiento'
    )
    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Precio unitario (congelado)'
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
    codigo_boleto = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        null=True,
        blank=True,
        verbose_name='Código único del boleto'
    )
    
    class Meta:
        verbose_name = 'Item Orden'
        verbose_name_plural = 'Items Orden'
        db_table = 'ventas_itemorden'
    
    def __str__(self):
        return f'Orden #{self.orden.id} - Asiento {self.asiento.numero} - ${self.precio_unitario}'
    
    @property
    def subtotal(self):
        """Retorna el subtotal (precio_unitario * cantidad, siempre 1 para asientos)."""
        return self.precio_unitario