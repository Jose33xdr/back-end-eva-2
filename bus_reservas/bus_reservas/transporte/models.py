"""
Modelos de la aplicación TRANSPORTE.

Define la estructura de datos para el sistema de reservas de bus:
- Ciudad: Ciudades de origen/destino
- Terminal: Terminales dentro de las ciudades
- Ruta: Conexiones entre terminales
- Bus: Vehículos con capacidad
- Servicio: Viajes programados (ruta + bus + fecha/hora + precio)
- Asiento: Asientos individuales de un servicio con estado de ocupación
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db.models import F, Q


class Ciudad(models.Model):
    """
    Modelo para ciudades de origen y destino.
    
    Ejemplos: Santiago, Temuco, Concepción
    """
    nombre = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Nombre de la ciudad'
    )
    
    class Meta:
        verbose_name = 'Ciudad'
        verbose_name_plural = 'Ciudades'
        ordering = ['nombre']
        db_table = 'transporte_ciudad'
    
    def __str__(self):
        return self.nombre


class Terminal(models.Model):
    """
    Modelo para terminales de buses.
    
    Cada terminal pertenece a una ciudad.
    Ejemplo: Terminal Santiago, Terminal Temuco
    """
    nombre = models.CharField(
        max_length=100,
        verbose_name='Nombre del terminal'
    )
    ciudad = models.ForeignKey(
        Ciudad,
        on_delete=models.CASCADE,
        related_name='terminales',
        verbose_name='Ciudad'
    )
    
    class Meta:
        verbose_name = 'Terminal'
        verbose_name_plural = 'Terminales'
        ordering = ['ciudad__nombre', 'nombre']
        db_table = 'transporte_terminal'
    
    def __str__(self):
        return f'{self.nombre} ({self.ciudad.nombre})'


class Ruta(models.Model):
    """
    Modelo para rutas entre terminales.
    
    Define origen, destino y distancia.
    """
    origen = models.ForeignKey(
        Terminal,
        on_delete=models.CASCADE,
        related_name='rutas_origen',
        verbose_name='Terminal de origen'
    )
    destino = models.ForeignKey(
        Terminal,
        on_delete=models.CASCADE,
        related_name='rutas_destino',
        verbose_name='Terminal de destino'
    )
    distancia_km = models.PositiveIntegerField(
        verbose_name='Distancia en kilómetros'
    )
    
    class Meta:
        verbose_name = 'Ruta'
        verbose_name_plural = 'Rutas'
        ordering = ['origen__ciudad__nombre', 'destino__ciudad__nombre']
        db_table = 'transporte_ruta'
        # Evitar rutas duplicadas mismo origen-destino
        constraints = [
            models.UniqueConstraint(
                fields=['origen', 'destino'],
                name='unique_ruta_origen_destino'
            )
        ]
    
    def __str__(self):
        return f'{self.origen} → {self.destino} ({self.distancia_km} km)'


class Bus(models.Model):
    """
    Modelo para buses/vehículos.
    
    Ejemplo: Mercedes Benz, capacidad 30 pasajeros
    """
    patente = models.CharField(
        max_length=10,
        unique=True,
        verbose_name='Patente'
    )
    marca = models.CharField(
        max_length=50,
        verbose_name='Marca'
    )
    modelo = models.CharField(
        max_length=50,
        verbose_name='Modelo'
    )
    capacidad = models.PositiveIntegerField(
        verbose_name='Capacidad (número de asientos)'
    )
    cantidad_cama = models.PositiveIntegerField(
        default=0,
        verbose_name='Cantidad de asientos cama'
    )
    
    class Meta:
        verbose_name = 'Bus'
        verbose_name_plural = 'Buses'
        ordering = ['patente']
        db_table = 'transporte_bus'
        constraints = [
            models.CheckConstraint(
                condition=Q(cantidad_cama__lte=F('capacidad')),
                name='cantidad_cama_no_supera_capacidad',
            )
        ]
    
    def __str__(self):
        return f'{self.patente} - {self.marca} {self.modelo} ({self.capacidad} asientos)'


class Servicio(models.Model):
    """
    Modelo para servicios (viajes programados).
    
    Combina una ruta, un bus, fecha/hora de salida y precio base.
    """
    ruta = models.ForeignKey(
        Ruta,
        on_delete=models.CASCADE,
        related_name='servicios',
        verbose_name='Ruta'
    )
    bus = models.ForeignKey(
        Bus,
        on_delete=models.CASCADE,
        related_name='servicios',
        verbose_name='Bus'
    )
    fecha_salida = models.DateField(
        verbose_name='Fecha de salida'
    )
    hora_salida = models.TimeField(
        verbose_name='Hora de salida'
    )
    precio_base = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Precio base'
    )
    precio_cama = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Tarifa cama'
    )
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Servicio'
        verbose_name_plural = 'Servicios'
        ordering = ['fecha_salida', 'hora_salida']
        db_table = 'transporte_servicio'
    
    def __str__(self):
        return f'{self.ruta} - {self.fecha_salida} {self.hora_salida} - ${self.precio_base}'
    
    @property
    def asientos_disponibles(self):
        """Retorna la cantidad de asientos disponibles en este servicio."""
        return self.asientos.filter(ocupado=False).count()
    
    @property
    def asientos_totales(self):
        """Retorna la capacidad total del bus."""
        return self.bus.capacidad


class Asiento(models.Model):
    """
    Modelo para asientos individuales de un servicio.
    
    Cada asiento pertenece a un servicio y tiene un número y estado de ocupación.
    Ejemplo: Asiento 1, Asiento 2, Asiento 3...
    """
    class Tipo(models.TextChoices):
        SEMICAMA = 'SEMICAMA', 'Semicama'
        CAMA = 'CAMA', 'Cama'

    numero = models.PositiveIntegerField(
        verbose_name='Número de asiento'
    )
    servicio = models.ForeignKey(
        Servicio,
        on_delete=models.CASCADE,
        related_name='asientos',
        verbose_name='Servicio'
    )
    ocupado = models.BooleanField(
        default=False,
        verbose_name='Ocupado'
    )
    tipo = models.CharField(
        max_length=10,
        choices=Tipo.choices,
        default=Tipo.SEMICAMA,
        verbose_name='Tipo de asiento'
    )
    
    class Meta:
        verbose_name = 'Asiento'
        verbose_name_plural = 'Asientos'
        ordering = ['servicio', 'numero']
        db_table = 'transporte_asiento'
        # Un asiento por número por servicio
        constraints = [
            models.UniqueConstraint(
                fields=['servicio', 'numero'],
                name='unique_asiento_servicio_numero'
            )
        ]
    
    def __str__(self):
        estado = 'Ocupado' if self.ocupado else 'Disponible'
        return f'Asiento {self.numero} {self.get_tipo_display()} - {self.servicio} ({estado})'

    @property
    def precio(self):
        if self.tipo == self.Tipo.CAMA:
            return self.servicio.precio_cama
        return self.servicio.precio_base