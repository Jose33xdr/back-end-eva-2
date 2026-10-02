"""
Admin de la aplicación VENTAS.

Registra los modelos Orden e ItemOrden en el panel de administración.
"""

from django.contrib import admin
from .models import Orden, ItemOrden


class ItemOrdenInline(admin.TabularInline):
    model = ItemOrden
    extra = 0
    readonly_fields = ['servicio', 'asiento', 'precio_unitario']
    can_delete = False


@admin.register(Orden)
class OrdenAdmin(admin.ModelAdmin):
    list_display = ['id', 'usuario', 'fecha', 'total', 'estado', 'cantidad_items']
    list_filter = ['estado', 'fecha', 'usuario']
    search_fields = ['usuario__username', 'usuario__email', 'id']
    ordering = ['-fecha']
    inlines = [ItemOrdenInline]
    readonly_fields = ['fecha', 'total']
    
    def cantidad_items(self, obj):
        return obj.items.count()
    cantidad_items.short_description = 'Items'


@admin.register(ItemOrden)
class ItemOrdenAdmin(admin.ModelAdmin):
    list_display = ['orden', 'servicio', 'asiento', 'precio_unitario']
    list_filter = ['orden__estado', 'servicio__fecha_salida']
    search_fields = ['orden__id', 'servicio__ruta__origen__ciudad__nombre', 'servicio__ruta__destino__ciudad__nombre']
    ordering = ['-orden__fecha']
    readonly_fields = ['orden', 'servicio', 'asiento', 'precio_unitario']