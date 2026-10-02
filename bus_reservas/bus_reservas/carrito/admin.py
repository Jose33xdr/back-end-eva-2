"""
Admin de la aplicación CARRITO.

Registra los modelos Carro e ItemCarro en el panel de administración.
"""

from django.contrib import admin
from .models import Carro, ItemCarro


class ItemCarroInline(admin.TabularInline):
    model = ItemCarro
    extra = 0
    readonly_fields = ['asiento', 'cantidad', 'fecha_agregado']
    can_delete = False


@admin.register(Carro)
class CarroAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'activo', 'fecha_creacion', 'total_items', 'total_precio']
    list_filter = ['activo', 'fecha_creacion']
    search_fields = ['usuario__username', 'usuario__email']
    ordering = ['-fecha_creacion']
    inlines = [ItemCarroInline]
    
    def total_items(self, obj):
        return obj.total_items
    total_items.short_description = 'Items'
    
    def total_precio(self, obj):
        return f'${obj.total_precio:,.0f}'
    total_precio.short_description = 'Total'


@admin.register(ItemCarro)
class ItemCarroAdmin(admin.ModelAdmin):
    list_display = ['carro', 'asiento', 'cantidad', 'fecha_agregado']
    list_filter = ['fecha_agregado']
    search_fields = ['carro__usuario__username', 'asiento__servicio__ruta__origen__ciudad__nombre']
    ordering = ['-fecha_agregado']