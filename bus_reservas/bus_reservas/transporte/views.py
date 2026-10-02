"""
Views de la aplicación TRANSPORTE.

ViewSets para CRUD de Ciudad, Terminal, Ruta, Bus, Servicio y Asiento.
Incluyen permisos por rol y filtros para Servicios.
"""

from rest_framework import viewsets, filters, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

from .models import Ciudad, Terminal, Ruta, Bus, Servicio, Asiento
from .serializers import (
    CiudadSerializer, TerminalSerializer, RutaSerializer,
    BusSerializer, ServicioSerializer, ServicioDetalleSerializer, AsientoSerializer
)
from usuarios.permissions import EsAdmin, EsPasajero, Publico


class CiudadViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de Ciudades.
    
    Permisos:
    - GET: Público (cualquiera puede ver ciudades)
    - POST/PUT/DELETE: Solo ADMINISTRADOR
    
    Endpoints:
    - GET /api/ciudades/
    - POST /api/ciudades/
    - GET /api/ciudades/{id}/
    - PUT/PATCH /api/ciudades/{id}/
    - DELETE /api/ciudades/{id}/
    """
    queryset = Ciudad.objects.all()
    serializer_class = CiudadSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre']
    ordering_fields = ['nombre']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [Publico()]
        return [EsAdmin()]


class TerminalViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de Terminales.
    
    Permisos:
    - GET: Público
    - POST/PUT/DELETE: Solo ADMINISTRADOR
    
    Endpoints:
    - GET /api/terminales/
    - POST /api/terminales/
    - GET /api/terminales/{id}/
    - PUT/PATCH /api/terminales/{id}/
    - DELETE /api/terminales/{id}/
    """
    queryset = Terminal.objects.select_related('ciudad').all()
    serializer_class = TerminalSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['ciudad']
    search_fields = ['nombre', 'ciudad__nombre']
    ordering_fields = ['nombre', 'ciudad__nombre']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [Publico()]
        return [EsAdmin()]


class RutaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de Rutas.
    
    Permisos:
    - GET: Público
    - POST/PUT/DELETE: Solo ADMINISTRADOR
    
    Endpoints:
    - GET /api/rutas/
    - POST /api/rutas/
    - GET /api/rutas/{id}/
    - PUT/PATCH /api/rutas/{id}/
    - DELETE /api/rutas/{id}/
    """
    queryset = Ruta.objects.select_related('origen__ciudad', 'destino__ciudad').all()
    serializer_class = RutaSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['origen__ciudad', 'destino__ciudad']
    search_fields = ['origen__nombre', 'destino__nombre', 'origen__ciudad__nombre', 'destino__ciudad__nombre']
    ordering_fields = ['distancia_km']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [Publico()]
        return [EsAdmin()]


class BusViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de Buses.
    
    Permisos:
    - GET: Público
    - POST/PUT/DELETE: Solo ADMINISTRADOR
    
    Endpoints:
    - GET /api/buses/
    - POST /api/buses/
    - GET /api/buses/{id}/
    - PUT/PATCH /api/buses/{id}/
    - DELETE /api/buses/{id}/
    """
    queryset = Bus.objects.all()
    serializer_class = BusSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['patente', 'marca', 'modelo']
    ordering_fields = ['patente', 'capacidad']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [Publico()]
        return [EsAdmin()]


class ServicioViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de Servicios (viajes programados).
    
    Permisos:
    - GET: Público (con filtros)
    - POST/PUT/DELETE: Solo ADMINISTRADOR
    
    Filtros disponibles:
    - origen: ciudad de origen (nombre)
    - destino: ciudad de destino (nombre)
    - fecha: fecha de salida (YYYY-MM-DD)
    - precio_min: precio mínimo
    - precio_max: precio máximo
    
    Endpoints:
    - GET /api/servicios/
    - POST /api/servicios/
    - GET /api/servicios/{id}/
    - PUT/PATCH /api/servicios/{id}/
    - DELETE /api/servicios/{id}/
    """
    queryset = Servicio.objects.select_related(
        'ruta__origen__ciudad', 'ruta__destino__ciudad', 'bus'
    ).prefetch_related('asientos').all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'ruta__origen__ciudad__nombre': ['exact', 'icontains'],
        'ruta__destino__ciudad__nombre': ['exact', 'icontains'],
        'fecha_salida': ['exact', 'gte', 'lte'],
        'precio_base': ['gte', 'lte'],
    }
    search_fields = ['ruta__origen__ciudad__nombre', 'ruta__destino__ciudad__nombre', 'bus__patente']
    ordering_fields = ['fecha_salida', 'hora_salida', 'precio_base']
    ordering = ['fecha_salida', 'hora_salida']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ServicioDetalleSerializer
        return ServicioSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'buscar', 'asientos']:
            return [Publico()]
        return [EsAdmin()]

    @action(detail=False, methods=['get'], url_path='buscar')
    def buscar(self, request):
        """Expone la búsqueda pública de viajes con los filtros del listado."""
        return self.list(request)

    @action(detail=True, methods=['get'], url_path='asientos')
    def asientos(self, request, pk=None):
        """Lista los asientos disponibles y ocupados de un servicio."""
        servicio = self.get_object()
        serializer = AsientoSerializer(servicio.asientos.all(), many=True)
        return Response(serializer.data)
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtros personalizados por query params
        origen = self.request.query_params.get('origen')
        destino = self.request.query_params.get('destino')
        fecha = self.request.query_params.get('fecha')
        precio_min = self.request.query_params.get('precio_min')
        precio_max = self.request.query_params.get('precio_max')
        
        if origen:
            queryset = queryset.filter(ruta__origen__ciudad__nombre__icontains=origen)
        if destino:
            queryset = queryset.filter(ruta__destino__ciudad__nombre__icontains=destino)
        if fecha:
            queryset = queryset.filter(fecha_salida=fecha)
        if precio_min:
            queryset = queryset.filter(precio_base__gte=precio_min)
        if precio_max:
            queryset = queryset.filter(precio_base__lte=precio_max)
        
        return queryset


class AsientoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para consultar Asientos (solo lectura).
    
    Permisos:
    - GET: Público
    
    Endpoints:
    - GET /api/asientos/
    - GET /api/asientos/{id}/
    """
    queryset = Asiento.objects.select_related('servicio__ruta__origen__ciudad', 'servicio__ruta__destino__ciudad').all()
    serializer_class = AsientoSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['servicio', 'ocupado', 'tipo']
    ordering_fields = ['numero']
    
    def get_permissions(self):
        return [Publico()]