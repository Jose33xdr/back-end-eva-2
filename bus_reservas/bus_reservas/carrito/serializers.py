"""
Serializers de la aplicación CARRITO.

Transforman los datos del carrito y sus items para la API REST.
"""

from rest_framework import serializers
from .models import Carro, ItemCarro
from transporte.serializers import AsientoSerializer, ServicioSerializer
from usuarios.validators import documento_pasajero_valido


class ItemCarroSerializer(serializers.ModelSerializer):
    """
    Serializer para items del carrito.
    
    Incluye detalles del asiento y servicio para mostrar al usuario.
    """
    asiento_detalle = AsientoSerializer(source='asiento', read_only=True)
    servicio_detalle = ServicioSerializer(source='asiento.servicio', read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = ItemCarro
        fields = [
            'id', 'asiento', 'asiento_detalle', 'servicio_detalle', 'cantidad',
            'nombre_pasajero', 'documento_pasajero', 'subtotal', 'fecha_agregado'
        ]
        read_only_fields = ['fecha_agregado', 'subtotal']
        extra_kwargs = {
            'nombre_pasajero': {'required': True, 'allow_blank': False, 'allow_null': False},
            'documento_pasajero': {'required': True, 'allow_blank': False, 'allow_null': False},
        }

    def validate_documento_pasajero(self, value):
        if not documento_pasajero_valido(value):
            raise serializers.ValidationError('El RUT no es válido; revisa su dígito verificador.')
        return value


class CarroSerializer(serializers.ModelSerializer):
    """
    Serializer para el carrito completo.
    
    Incluye todos los items con sus detalles y totales calculados.
    """
    items = ItemCarroSerializer(many=True, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    total_precio = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Carro
        fields = ['id', 'usuario', 'activo', 'fecha_creacion', 'items', 'total_items', 'total_precio']
        read_only_fields = ['usuario', 'fecha_creacion', 'total_items', 'total_precio']


class AgregarAlCarroSerializer(serializers.Serializer):
    """
    Serializer para agregar un asiento al carrito.
    
    Recibe el ID del asiento a agregar.
    """
    asiento_id = serializers.IntegerField()
    nombre_pasajero = serializers.CharField(max_length=200)
    documento_pasajero = serializers.CharField(max_length=32)

    def validate_documento_pasajero(self, value):
        if not documento_pasajero_valido(value):
            raise serializers.ValidationError('El RUT no es válido; revisa su dígito verificador.')
        return value

    def validate_asiento_id(self, value):
        """Valida que el asiento exista y esté disponible."""
        from transporte.models import Asiento
        try:
            asiento = Asiento.objects.get(id=value)
        except Asiento.DoesNotExist:
            raise serializers.ValidationError('El asiento no existe.')
        
        if asiento.ocupado:
            raise serializers.ValidationError('El asiento ya está ocupado.')
        
        return value


class QuitarDelCarroSerializer(serializers.Serializer):
    """
    Serializer para quitar un item del carrito.
    
    Recibe el ID del item a quitar.
    """
    item_id = serializers.IntegerField()


class RespuestaDetalleSerializer(serializers.Serializer):
    """Standard message response for cart operations."""

    detail = serializers.CharField()