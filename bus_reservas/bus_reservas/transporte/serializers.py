"""
Serializers de la aplicación TRANSPORTE.

Transforman los datos de los modelos de transporte para la API REST.
Incluyen serializers para Ciudad, Terminal, Ruta, Bus, Servicio y Asiento.
"""

from rest_framework import serializers
from .models import Ciudad, Terminal, Ruta, Bus, Servicio, Asiento


class CiudadSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Ciudad.
    
    Serializa: id, nombre
    """
    class Meta:
        model = Ciudad
        fields = ['id', 'nombre']


class TerminalSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Terminal.
    
    Incluye el nombre de la ciudad relacionada para fácil lectura.
    Serializa: id, nombre, ciudad (id y nombre)
    """
    ciudad_nombre = serializers.CharField(source='ciudad.nombre', read_only=True)
    
    class Meta:
        model = Terminal
        fields = ['id', 'nombre', 'ciudad', 'ciudad_nombre']


class RutaSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Ruta.
    
    Incluye nombres de terminales origen y destino para fácil lectura.
    Serializa: id, origen, destino, distancia_km, nombres de terminales
    """
    origen_nombre = serializers.CharField(source='origen.nombre', read_only=True)
    origen_ciudad = serializers.CharField(source='origen.ciudad.nombre', read_only=True)
    destino_nombre = serializers.CharField(source='destino.nombre', read_only=True)
    destino_ciudad = serializers.CharField(source='destino.ciudad.nombre', read_only=True)
    
    class Meta:
        model = Ruta
        fields = [
            'id', 'origen', 'destino', 'distancia_km',
            'origen_nombre', 'origen_ciudad', 'destino_nombre', 'destino_ciudad'
        ]


class BusSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Bus.
    
    Serializa: id, patente, marca, modelo, capacidad
    """
    class Meta:
        model = Bus
        fields = ['id', 'patente', 'marca', 'modelo', 'capacidad', 'cantidad_cama']

    def validate(self, attrs):
        capacidad = attrs.get('capacidad', getattr(self.instance, 'capacidad', None))
        cantidad_cama = attrs.get(
            'cantidad_cama',
            getattr(self.instance, 'cantidad_cama', 0),
        )
        if capacidad is not None and cantidad_cama > capacidad:
            raise serializers.ValidationError({
                'cantidad_cama': 'No puede superar la capacidad total del bus.'
            })
        return attrs


class AsientoSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Asiento.
    
    Serializa: id, numero, tipo, precio y estado de ocupación
    """
    precio = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Asiento
        fields = ['id', 'numero', 'tipo', 'precio', 'ocupado']


class ServicioSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Servicio.
    
    Incluye información relacionada de ruta, bus y asientos disponibles.
    Serializa: todos los campos + info relacionada + asientos_disponibles
    """
    ruta_origen = serializers.CharField(source='ruta.origen.ciudad.nombre', read_only=True)
    ruta_destino = serializers.CharField(source='ruta.destino.ciudad.nombre', read_only=True)
    bus_patente = serializers.CharField(source='bus.patente', read_only=True)
    bus_capacidad = serializers.IntegerField(source='bus.capacidad', read_only=True)
    asientos_disponibles = serializers.IntegerField(read_only=True)
    asientos_totales = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Servicio
        fields = [
            'id', 'ruta', 'bus', 'fecha_salida', 'hora_salida', 'precio_base', 'precio_cama',
            'ruta_origen', 'ruta_destino', 'bus_patente', 'bus_capacidad',
            'asientos_disponibles', 'asientos_totales', 'creado', 'actualizado'
        ]
        read_only_fields = ['creado', 'actualizado']


class ServicioDetalleSerializer(ServicioSerializer):
    """
    Serializer extendido para detalle de servicio.
    
    Incluye la lista completa de asientos con su estado.
    """
    asientos = AsientoSerializer(many=True, read_only=True)
    
    class Meta(ServicioSerializer.Meta):
        fields = ServicioSerializer.Meta.fields + ['asientos']