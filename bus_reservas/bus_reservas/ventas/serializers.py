"""
Serializers de la aplicación VENTAS.

Transforman los datos de órdenes e items para la API REST.
"""

from rest_framework import serializers
from .models import Orden, ItemOrden
from transporte.serializers import ServicioSerializer, AsientoSerializer


class ItemOrdenSerializer(serializers.ModelSerializer):
    """
    Serializer para items de orden.
    
    Incluye detalles del servicio y asiento para visualización.
    El precio_unitario viene congelado de la compra.
    """
    servicio_detalle = ServicioSerializer(source='servicio', read_only=True)
    asiento_detalle = AsientoSerializer(source='asiento', read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = ItemOrden
        fields = [
            'id', 'servicio', 'servicio_detalle', 'asiento', 'asiento_detalle',
            'precio_unitario', 'nombre_pasajero', 'documento_pasajero',
            'codigo_boleto', 'subtotal'
        ]
        read_only_fields = ['precio_unitario', 'codigo_boleto']


class OrdenSerializer(serializers.ModelSerializer):
    """
    Serializer para órdenes.
    
    Incluye items con detalles y total calculado.
    """
    items = ItemOrdenSerializer(many=True, read_only=True)
    usuario_nombre = serializers.CharField(source='usuario.username', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    
    class Meta:
        model = Orden
        fields = [
            'id', 'usuario', 'usuario_nombre', 'fecha', 'total',
            'estado', 'estado_display', 'items'
        ]
        read_only_fields = ['usuario', 'fecha', 'total', 'estado']


class OrdenListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listado de órdenes.
    """
    usuario_nombre = serializers.CharField(source='usuario.username', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    cantidad_items = serializers.SerializerMethodField()
    
    class Meta:
        model = Orden
        fields = ['id', 'usuario_nombre', 'fecha', 'total', 'estado', 'estado_display', 'cantidad_items']
    
    def get_cantidad_items(self, obj) -> int:
        return obj.items.count()


class CambioEstadoSerializer(serializers.Serializer):
    """
    Serializer para cambio de estado de orden (solo administrador).
    """
    estado = serializers.ChoiceField(choices=Orden.Estado.choices)
    
    def validate_estado(self, value):
        """Validaciones de transición de estados."""
        # Las validaciones de transición se hacen en la vista
        return value


class CheckoutSerializer(serializers.Serializer):
    """
    Serializer para el proceso de checkout.
    
    No requiere datos adicionales - usa el carrito del usuario.
    """
    pass