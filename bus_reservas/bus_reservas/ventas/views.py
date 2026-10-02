"""
Views de la aplicación VENTAS.

Implementa:
- Checkout transaccional: crear orden desde carrito, validar disponibilidad
- Control de stock: marcar asientos como ocupados al pagar (PENDIENTE -> PAGADO)
- Liberación de stock: liberar asientos al cancelar (PAGADO -> CANCELADO)
- Listado de órdenes del usuario
- Cambio de estado por administrador
"""

from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .models import Orden, ItemOrden
from .serializers import (
    CambioEstadoSerializer, CheckoutSerializer, ItemOrdenSerializer,
    OrdenListSerializer, OrdenSerializer,
)
from carrito.models import Carro, ItemCarro
from transporte.models import Asiento
from usuarios.permissions import EsPasajero, EsAdmin
from .services import (
    InvalidOrderTransition,
    SeatUnavailable,
    cambiar_estado_orden as actualizar_estado_orden,
)


class MisOrdenesView(generics.ListAPIView):
    """
    Vista para listar las órdenes del usuario autenticado.
    
    Endpoint: GET /api/mis-reservas/
    """
    serializer_class = OrdenListSerializer
    permission_classes = [IsAuthenticated, EsPasajero]
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Orden.objects.none()
        return Orden.objects.filter(usuario=self.request.user).prefetch_related(
            'items__servicio__ruta__origen__ciudad',
            'items__servicio__ruta__destino__ciudad',
            'items__asiento'
        )


class MisBoletosView(generics.ListAPIView):
    """Lista los boletos pagados o entregados del pasajero autenticado."""
    serializer_class = ItemOrdenSerializer
    permission_classes = [IsAuthenticated, EsPasajero]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return ItemOrden.objects.none()
        return ItemOrden.objects.filter(
            orden__usuario=self.request.user,
            orden__estado__in=[Orden.Estado.PAGADO, Orden.Estado.ENTREGADO],
        ).select_related(
            'orden', 'servicio__ruta__origen__ciudad',
            'servicio__ruta__destino__ciudad', 'asiento'
        ).order_by('orden__fecha', 'pk')


class OrdenDetalleView(generics.RetrieveAPIView):
    """
    Vista para ver detalle de una orden propia.
    
    Endpoint: GET /api/ventas/{id}/
    """
    serializer_class = OrdenSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Usuarios ven solo sus órdenes, admins ven todas
        if getattr(self, 'swagger_fake_view', False):
            return Orden.objects.none()
        if self.request.user.is_admin():
            return Orden.objects.all().prefetch_related('items__servicio', 'items__asiento')
        return Orden.objects.filter(usuario=self.request.user).prefetch_related('items__servicio', 'items__asiento')


@extend_schema(
    request=CheckoutSerializer,
    responses={201: OrdenSerializer},
    description='Valida los asientos del carro y crea una orden pendiente.',
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, EsPasajero])
def checkout(request):
    """
    Procesa el checkout: crea una orden desde el carrito del usuario.
    
    Flujo:
    1. Obtiene items del carrito
    2. Valida que los asientos estén disponibles (no ocupados)
    3. Crea la Orden con estado PENDIENTE
    4. Crea ItemsOrden con precios congelados
    5. NO descuenta stock (asientos quedan disponible hasta pagar)
    6. Vacía el carrito
    
    Endpoint: POST /api/ventas/checkout/
    """
    serializer = CheckoutSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    # Obtener carrito del usuario
    try:
        carro = Carro.objects.get(usuario=request.user, activo=True)
    except Carro.DoesNotExist:
        return Response(
            {'error': 'No tienes un carrito activo.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    items_carro = carro.items.select_related('asiento__servicio').all()
    
    if not items_carro.exists():
        return Response(
            {'error': 'Tu carrito está vacío.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    with transaction.atomic():
        asientos = list(
            Asiento.objects.select_for_update()
            .filter(pk__in=[item.asiento_id for item in items_carro])
            .order_by('pk')
        )
        asientos_por_id = {asiento.pk: asiento for asiento in asientos}
        no_disponibles = [
            asiento.numero for asiento in asientos if asiento.ocupado
        ]
        if no_disponibles:
            return Response(
                {
                    'error': 'Algunos asientos ya no están disponibles.',
                    'asientos_no_disponibles': no_disponibles,
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        total = sum(
            asientos_por_id[item.asiento_id].precio * item.cantidad
            for item in items_carro
        )
        orden = Orden.objects.create(
            usuario=request.user,
            total=total,
            estado=Orden.Estado.PENDIENTE
        )
        ItemOrden.objects.bulk_create([
            ItemOrden(
                orden=orden,
                servicio=item.asiento.servicio,
                asiento=item.asiento,
                precio_unitario=asientos_por_id[item.asiento_id].precio,
                nombre_pasajero=item.nombre_pasajero,
                documento_pasajero=item.documento_pasajero,
            )
            for item in items_carro
        ])
        orden = actualizar_estado_orden(orden.pk, Orden.Estado.PAGADO)
        items_carro.delete()
    
    return Response(
        OrdenSerializer(orden).data,
        status=status.HTTP_201_CREATED
    )


@extend_schema(
    request=CambioEstadoSerializer,
    responses={
        200: OrdenSerializer,
        400: OpenApiResponse(description='Transición inválida o asiento no disponible.'),
    },
    description='Actualiza el estado de una orden y sincroniza la ocupación de asientos.',
)
@api_view(['PATCH'])
@permission_classes([IsAuthenticated, EsAdmin])
def cambiar_estado_orden(request, orden_id):
    """
    Cambia el estado de una orden (solo administrador).
    
    Lógica de transiciones:
    - PENDIENTE -> PAGADO: Validar disponibilidad, marcar asientos como ocupados
    - PAGADO -> CANCELADO: Liberar asientos (ocupado=False)
    - Otros cambios: Solo actualizar estado
    
    Endpoint: PATCH /api/ventas/{id}/estado/
    Body: {"estado": "PAGADO"}
    """
    serializer = CambioEstadoSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    nuevo_estado = serializer.validated_data['estado']
    try:
        orden = actualizar_estado_orden(orden_id, nuevo_estado)
    except Orden.DoesNotExist:
        return Response({'detail': 'Orden no encontrada.'}, status=status.HTTP_404_NOT_FOUND)
    except (InvalidOrderTransition, SeatUnavailable) as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    return Response(
        OrdenSerializer(orden).data,
        status=status.HTTP_200_OK
    )


# Vista para que admin vea todas las órdenes
class AdminOrdenesView(generics.ListAPIView):
    """
    Vista para que administrador vea todas las órdenes.
    
    Endpoint: GET /api/ventas/ (solo admin)
    """
    serializer_class = OrdenListSerializer
    permission_classes = [IsAuthenticated, EsAdmin]
    queryset = Orden.objects.all().prefetch_related('items__servicio', 'items__asiento').select_related('usuario')