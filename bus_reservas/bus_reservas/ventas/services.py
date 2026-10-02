"""Transactional order-state changes and seat availability enforcement."""

from django.db import transaction

from transporte.models import Asiento
from .models import Orden


class InvalidOrderTransition(Exception):
    """Raised when an order attempts a state transition outside the lifecycle."""

    pass


class SeatUnavailable(Exception):
    """Raised when a requested seat is already sold."""

    pass


@transaction.atomic
def cambiar_estado_orden(orden_id, nuevo_estado):
    orden = Orden.objects.select_for_update().get(pk=orden_id)
    transiciones_validas = {
        Orden.Estado.PENDIENTE: [Orden.Estado.PAGADO, Orden.Estado.CANCELADO],
        Orden.Estado.PAGADO: [Orden.Estado.ENTREGADO, Orden.Estado.CANCELADO],
        Orden.Estado.ENTREGADO: [],
        Orden.Estado.CANCELADO: [],
    }

    if nuevo_estado not in transiciones_validas[orden.estado]:
        raise InvalidOrderTransition(
            f'No se puede cambiar de {orden.estado} a {nuevo_estado}.'
        )

    items = list(orden.items.all())
    asientos = list(
        Asiento.objects.select_for_update()
        .filter(pk__in=[item.asiento_id for item in items])
        .order_by('pk')
    )

    if orden.estado == Orden.Estado.PENDIENTE and nuevo_estado == Orden.Estado.PAGADO:
        fuera_de_capacidad = [
            asiento.numero
            for asiento in asientos
            if asiento.numero > asiento.servicio.bus.capacidad
        ]
        if fuera_de_capacidad:
            numeros = ', '.join(str(numero) for numero in fuera_de_capacidad)
            raise SeatUnavailable(
                f'Los asientos {numeros} superan la capacidad del bus.'
            )
        ocupados = [asiento.numero for asiento in asientos if asiento.ocupado]
        if ocupados:
            numeros = ', '.join(str(numero) for numero in ocupados)
            raise SeatUnavailable(f'Los asientos {numeros} ya no están disponibles.')
        for asiento in asientos:
            asiento.ocupado = True
        Asiento.objects.bulk_update(asientos, ['ocupado'])

    elif orden.estado == Orden.Estado.PAGADO and nuevo_estado == Orden.Estado.CANCELADO:
        for asiento in asientos:
            asiento.ocupado = False
        Asiento.objects.bulk_update(asientos, ['ocupado'])

    orden.estado = nuevo_estado
    orden.save(update_fields=['estado'])
    return orden
