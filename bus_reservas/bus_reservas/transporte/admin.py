"""
Admin de la aplicación TRANSPORTE.

Registra todos los modelos de transporte en el panel de administración de Django.
"""

from django.contrib import admin
from .models import Ciudad, Terminal, Ruta, Bus, Servicio, Asiento


@admin.register(Ciudad)
class CiudadAdmin(admin.ModelAdmin):
    """Administra las ciudades visibles en la API y el portal web."""
    list_display = ['nombre']
    search_fields = ['nombre']
    ordering = ['nombre']


@admin.register(Terminal)
class TerminalAdmin(admin.ModelAdmin):
    """Administra terminales y su relaci?n con cada ciudad."""
    list_display = ['nombre', 'ciudad']
    list_filter = ['ciudad']
    search_fields = ['nombre', 'ciudad__nombre']
    ordering = ['ciudad__nombre', 'nombre']


@admin.register(Ruta)
class RutaAdmin(admin.ModelAdmin):
    """Administra rutas y conexiones entre terminales."""
    list_display = ['origen', 'destino', 'distancia_km']
    list_filter = ['origen__ciudad', 'destino__ciudad']
    search_fields = ['origen__nombre', 'destino__nombre', 'origen__ciudad__nombre', 'destino__ciudad__nombre']
    ordering = ['origen__ciudad__nombre', 'destino__ciudad__nombre']


@admin.register(Bus)
class BusAdmin(admin.ModelAdmin):
    """Administra los buses y su capacidad f?sica."""
    list_display = ['patente', 'marca', 'modelo', 'capacidad']
    search_fields = ['patente', 'marca', 'modelo']
    ordering = ['patente']


class AsientoInline(admin.TabularInline):
    """Muestra los asientos ya generados para cada servicio."""
    model = Asiento
    extra = 0
    readonly_fields = ['numero', 'ocupado']
    can_delete = False
    max_num = 0


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    """Administra viajes y la asignaci?n autom?tica de asientos."""
    list_display = ['ruta', 'bus', 'fecha_salida', 'hora_salida', 'precio_base', 'asientos_disponibles']
    list_filter = ['fecha_salida', 'ruta__origen__ciudad', 'ruta__destino__ciudad', 'bus']
    search_fields = ['ruta__origen__ciudad__nombre', 'ruta__destino__ciudad__nombre', 'bus__patente']
    ordering = ['-fecha_salida', 'hora_salida']
    inlines = [AsientoInline]
    
    def asientos_disponibles(self, obj):
        return obj.asientos_disponibles
    asientos_disponibles.short_description = 'Disponibles'


@admin.register(Asiento)
class AsientoAdmin(admin.ModelAdmin):
    """Consulta y ajuste del estado de cada asiento por servicio."""
    list_display = ['servicio', 'numero', 'ocupado']
    list_filter = ['ocupado', 'servicio__fecha_salida']
    search_fields = ['servicio__ruta__origen__ciudad__nombre', 'servicio__ruta__destino__ciudad__nombre']
    ordering = ['servicio', 'numero']