"""
Views de la aplicación CARRITO.

Endpoints para gestionar el carrito del pasajero:
- Ver carrito
- Agregar asiento
- Quitar asiento
"""

from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse
from django.shortcuts import get_object_or_404

from .models import Carro, ItemCarro
from .serializers import (
    AgregarAlCarroSerializer,
    CarroSerializer,
    ItemCarroSerializer,
    RespuestaDetalleSerializer,
)
from transporte.models import Asiento
from usuarios.permissions import EsPasajero


class CarroView(generics.RetrieveAPIView):
    """
    Vista para obtener el carrito del usuario autenticado.
    
    Si no existe, lo crea automáticamente.
    Endpoint: GET /api/carrito/
    """
    serializer_class = CarroSerializer
    permission_classes = [IsAuthenticated, EsPasajero]
    
    def get_object(self):
        carro, _ = Carro.objects.get_or_create(usuario=self.request.user, activo=True)
        return carro


@extend_schema(
    request=AgregarAlCarroSerializer,
    responses={201: ItemCarroSerializer},
    description='Agrega al carro un asiento e identifica a su ocupante.',
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, EsPasajero])
def agregar_al_carro(request):
    """
    Agrega un asiento al carrito del usuario.
    
    NO bloquea el asiento (ocupado=False se mantiene).
    El asiento solo se marca como ocupado al pagar la orden.
    
    Endpoint: POST /api/carrito/agregar/
    Body: {"asiento_id": 1}
    """
    serializer = AgregarAlCarroSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    asiento_id = serializer.validated_data['asiento_id']
    asiento = get_object_or_404(Asiento, id=asiento_id)
    
    # Verificar que el asiento no esté ocupado
    if asiento.ocupado:
        return Response(
            {'error': 'El asiento ya está ocupado.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    if asiento.numero > asiento.servicio.bus.capacidad:
        return Response(
            {'error': 'El asiento supera la capacidad del bus.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Obtener o crear carrito del usuario
    carro, _ = Carro.objects.get_or_create(usuario=request.user, activo=True)
    
    # Verificar si ya está en el carrito
    if ItemCarro.objects.filter(carro=carro, asiento=asiento).exists():
        return Response(
            {'error': 'Este asiento ya está en tu carrito.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Crear item en el carrito
    item = ItemCarro.objects.create(
        carro=carro,
        asiento=asiento,
        cantidad=1,
        nombre_pasajero=serializer.validated_data['nombre_pasajero'],
        documento_pasajero=serializer.validated_data['documento_pasajero'],
    )
    
    return Response(
        ItemCarroSerializer(item).data,
        status=status.HTTP_201_CREATED
    )


@extend_schema(
    request=None,
    responses={200: RespuestaDetalleSerializer},
    description='Quita un asiento del carro del pasajero autenticado.',
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated, EsPasajero])
def quitar_del_carro(request, item_id):
    """
    Quita un item del carrito del usuario.
    
    Endpoint: DELETE /api/carrito/quitar/{item_id}/
    """
    item = get_object_or_404(ItemCarro, id=item_id, carro__usuario=request.user)
    item.delete()
    
    return Response(
        {'detail': 'Asiento quitado del carrito correctamente.'},
        status=status.HTTP_200_OK
    )


@extend_schema(
    request=None,
    responses={200: RespuestaDetalleSerializer},
    description='Elimina todos los asientos del carro activo.',
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated, EsPasajero])
def limpiar_carro(request):
    """
    Vacía completamente el carrito del usuario.
    
    Endpoint: DELETE /api/carrito/limpiar/
    """
    carro = get_object_or_404(Carro, usuario=request.user, activo=True)
    carro.items.all().delete()
    
    return Response(
        {'detail': 'Carrito vaciado correctamente.'},
        status=status.HTTP_200_OK
    )