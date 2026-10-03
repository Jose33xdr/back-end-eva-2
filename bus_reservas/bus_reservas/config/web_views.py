"""Server-rendered pages for passengers and fleet administrators."""

from datetime import date

from django import forms
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, Q
from django.db.models.deletion import ProtectedError
from django.forms import modelform_factory
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.timezone import localdate

from carrito.models import Carro, ItemCarro
from transporte.models import Asiento, Bus, Ciudad, Ruta, Servicio, Terminal
from usuarios.forms import RegistroUsuarioForm
from usuarios.validators import documento_pasajero_valido
from ventas.models import ItemOrden, Orden
from ventas.services import (
    InvalidOrderTransition,
    SeatUnavailable,
    cambiar_estado_orden,
)


def pagina_no_encontrada(request, exception=None):
    """Muestra la pagina 404 del portal web cuando la ruta no existe."""
    return render(request, 'web/404.html', status=404)


def documentacion_web(request, documento):
    """Carga la documentacion embebida de Swagger, Redoc o OpenAPI."""
    documento_urls = {
        'swagger': ('swagger-embedded', 'Swagger Docs'),
        'redoc': ('redoc-embedded', 'ReDoc'),
        'openapi': ('schema', 'OpenAPI'),
    }
    url_name, titulo = documento_urls[documento]
    return render(request, 'web/documentacion.html', {
        'documento_url': reverse(url_name),
        'documento_titulo': titulo,
        'mostrar_esquema': documento == 'openapi',
    })


def home(request):
    """Presenta la portada con viajes activos y datos resumidos del catalogo."""
    servicios_activos = (
        Servicio.objects.select_related(
            'ruta__origen__ciudad', 'ruta__destino__ciudad', 'bus'
        )
        .filter(fecha_salida__gte=localdate())
        .annotate(
            disponibles=Count('asientos', filter=Q(asientos__ocupado=False))
        )
        .filter(disponibles__gt=0)
    )
    servicios = servicios_activos.order_by('fecha_salida', 'hora_salida')[:6]
    return render(request, 'base.html', {
        'servicios': servicios,
        'ciudades': Ciudad.objects.order_by('nombre'),
        'rutas_total': Ruta.objects.count(),
        'servicios_total': servicios_activos.count(),
        'asientos_total': Asiento.objects.filter(
            ocupado=False,
            servicio__fecha_salida__gte=localdate(),
        ).count(),
        'ciudades_total': Ciudad.objects.count(),
    })


def buscar_viajes(request):
    """Busca servicios disponibles segun origen, destino, fecha y cantidad de pasajeros."""
    servicios = (
        Servicio.objects.select_related(
            'ruta__origen__ciudad', 'ruta__destino__ciudad', 'bus'
        )
        .annotate(
            disponibles=Count('asientos', filter=Q(asientos__ocupado=False))
        )
        .filter(fecha_salida__gte=localdate(), disponibles__gt=0)
    )
    origen = request.GET.get('origen', '').strip()
    destino = request.GET.get('destino', '').strip()
    fecha = request.GET.get('fecha', '').strip()
    pasajeros = request.GET.get('pasajeros', '1').strip()

    if origen:
        servicios = servicios.filter(ruta__origen__ciudad__nombre=origen)
    if destino:
        servicios = servicios.filter(ruta__destino__ciudad__nombre=destino)
    if fecha:
        try:
            date.fromisoformat(fecha)
        except ValueError:
            messages.error(request, 'La fecha indicada no es válida.')
            fecha = ''
        else:
            servicios = servicios.filter(fecha_salida=fecha)

    try:
        cantidad_pasajeros = int(pasajeros)
        if not 1 <= cantidad_pasajeros <= 8:
            raise ValueError
    except ValueError:
        messages.error(request, 'Selecciona entre 1 y 8 pasajeros.')
        cantidad_pasajeros = 1
    servicios = servicios.filter(disponibles__gte=cantidad_pasajeros)

    return render(request, 'web/resultados.html', {
        'servicios': servicios.order_by('fecha_salida', 'hora_salida'),
        'ciudades': Ciudad.objects.order_by('nombre'),
        'origen': origen,
        'destino': destino,
        'fecha': fecha,
        'pasajeros': cantidad_pasajeros,
    })


def iniciar_sesion(request):
    """Autentica a un usuario y redirige segun su rol y la URL de retorno."""
    if request.user.is_authenticated:
        return redirect('home')
    next_url = request.POST.get('next') or request.GET.get('next', '')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        usuario = authenticate(request, username=username, password=password)
        if usuario is not None:
            login(request, usuario)
            if next_url and url_has_allowed_host_and_scheme(
                next_url, allowed_hosts={request.get_host()}
            ):
                return redirect(next_url)
            if usuario.is_admin():
                return redirect('gestion-inicio')
            return redirect('home')
        messages.error(request, 'El usuario o la contraseña no son correctos.')
    return render(request, 'web/login.html', {'next': next_url})


def registro(request):
    """Registra un nuevo pasajero desde el portal web y lo conecta al sistema."""
    if request.user.is_authenticated:
        return redirect('home')
    form = RegistroUsuarioForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        usuario = form.save()
        login(request, usuario)
        messages.success(request, 'Tu cuenta quedó creada. Ya puedes buscar viajes.')
        return redirect('home')
    return render(request, 'web/registro.html', {'form': form})


@login_required
def cerrar_sesion(request):
    """Cierra la sesion del usuario con una validacion explicita via POST."""
    if request.method != 'POST':
        return HttpResponseForbidden('El cierre de sesión debe enviarse mediante POST.')
    logout(request)
    return redirect('home')


def pasajero_requerido(view):
    """Envuelve una vista y exige que el usuario tenga rol de pasajero."""
    @login_required
    def wrapped(request, *args, **kwargs):
        if not request.user.is_pasajero():
            return HttpResponseForbidden('Esta sección es solo para pasajeros.')
        return view(request, *args, **kwargs)
    return wrapped


def admin_requerido(view):
    """Envuelve una vista y exige permisos de administrador del portal."""
    @login_required
    def wrapped(request, *args, **kwargs):
        if not request.user.is_admin():
            return HttpResponseForbidden('Esta sección es solo para administradores.')
        return view(request, *args, **kwargs)
    return wrapped


def detalle_servicio(request, servicio_id):
    """Muestra el detalle del servicio y el mapa de asientos con validaciones de compra."""
    solo_lectura = request.GET.get('solo_lectura') == '1'
    if request.method == 'POST' and solo_lectura:
        return HttpResponseForbidden('Este mapa de asientos es solo para consulta.')

    servicio = get_object_or_404(
        Servicio.objects.select_related(
            'ruta__origen__ciudad', 'ruta__destino__ciudad', 'bus'
        ),
        pk=servicio_id,
    )
    asientos = servicio.asientos.filter(
        numero__lte=servicio.bus.capacidad
    ).order_by('numero')
    asientos_lista = list(asientos)
    seat_rows = [
        [
            {'asiento': asiento, 'position': (index % 4) + 1}
            for index, asiento in enumerate(asientos_lista[start:start + 4], start)
        ]
        for start in range(0, len(asientos_lista), 4)
    ]
    asientos_disponibles = asientos.filter(
        ocupado=False, numero__lte=servicio.bus.capacidad
    )
    asientos_ocupados = asientos.filter(ocupado=True).count()
    limite_compra = min(
        asientos_disponibles.count(),
        max(servicio.bus.capacidad - asientos_ocupados, 0),
    )
    asientos_seleccionados = []
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect(f'/login/?next={request.path}')
        if not request.user.is_pasajero():
            return HttpResponseForbidden('Solo los pasajeros pueden reservar asientos.')
        asientos_seleccionados = request.POST.getlist('asientos_ids')
        nombre_comprador = request.POST.get('nombre_comprador', '').strip()
        documento_comprador = request.POST.get('documento_pasajero', '').strip()
        if not asientos_seleccionados:
            messages.error(request, 'Selecciona al menos un asiento.')
        elif len(set(asientos_seleccionados)) != len(asientos_seleccionados):
            messages.error(request, 'No puedes seleccionar el mismo asiento más de una vez.')
        elif len(asientos_seleccionados) > limite_compra:
            messages.error(request, 'La cantidad seleccionada supera los asientos disponibles del bus.')
        elif any(
            not Asiento.objects.filter(
                pk=asiento_id, servicio=servicio, numero__lte=servicio.bus.capacidad
            ).exists()
            for asiento_id in asientos_seleccionados
        ):
            messages.error(request, 'La selección supera los asientos disponibles del bus.')
        elif not nombre_comprador:
            messages.error(request, 'Indica el nombre completo de quien realiza la compra.')
        elif not documento_comprador:
            messages.error(request, 'Indica el RUT o pasaporte de quien realiza la compra.')
        elif not documento_pasajero_valido(documento_comprador):
            messages.error(request, 'El RUT no es válido. Revisa el dígito verificador o ingresa un pasaporte.')
        else:
            carro, _ = Carro.objects.get_or_create(usuario=request.user, activo=True)
            with transaction.atomic():
                asientos_bloqueados = list(
                    Asiento.objects.select_for_update()
                    .filter(
                        pk__in=asientos_seleccionados,
                        servicio=servicio,
                        numero__lte=servicio.bus.capacidad,
                    )
                    .order_by('pk')
                )
                ocupados = [asiento.numero for asiento in asientos_bloqueados if asiento.ocupado]
                capacidad_restante = servicio.bus.capacidad - asientos.filter(
                    ocupado=True
                ).count()
                if (
                    len(asientos_bloqueados) != len(asientos_seleccionados)
                    or ocupados
                    or len(asientos_seleccionados) > capacidad_restante
                ):
                    messages.error(request, 'Uno o más asientos ya no están disponibles. Selecciónalos nuevamente.')
                else:
                    asientos_por_id = {str(asiento.pk): asiento for asiento in asientos_bloqueados}
                    for asiento in asientos_bloqueados:
                        ItemCarro.objects.update_or_create(
                            carro=carro,
                            asiento=asiento,
                            defaults={
                                'cantidad': 1,
                                'nombre_pasajero': nombre_comprador,
                                'documento_pasajero': documento_comprador,
                            },
                        )
                    messages.success(
                        request,
                        f'{len(asientos_bloqueados)} pasaje(s) añadido(s) a tu carro.',
                    )
                    return redirect('carro-web')
    return render(request, 'web/servicio.html', {
        'servicio': servicio,
        'asientos': asientos,
        'seat_rows': seat_rows,
        'asientos_disponibles': asientos_disponibles,
        'asientos_seleccionados': asientos_seleccionados,
        'nombre_comprador': request.POST.get('nombre_comprador', ''),
        'documento_comprador': request.POST.get('documento_pasajero', ''),
        'limite_compra': limite_compra,
        'solo_lectura': solo_lectura,
    })


@pasajero_requerido
def carro(request):
    """Muestra el carrito activo del pasajero para revisar y confirmar su compra."""
    carro_obj, _ = Carro.objects.get_or_create(usuario=request.user, activo=True)
    items = carro_obj.items.select_related(
        'asiento__servicio__ruta__origen__ciudad',
        'asiento__servicio__ruta__destino__ciudad',
    ).order_by('asiento__servicio__fecha_salida', 'asiento__numero')
    return render(request, 'web/carro.html', {
        'carro': carro_obj,
        'items': items,
    })


@pasajero_requerido
def quitar_item_carro(request, item_id):
    """Elimina un asiento del carrito y vuelve al resumen del carro."""
    if request.method != 'POST':
        return HttpResponseForbidden('La eliminación debe enviarse mediante POST.')
    item = get_object_or_404(ItemCarro, pk=item_id, carro__usuario=request.user)
    item.delete()
    messages.success(request, 'El asiento fue quitado del carro.')
    return redirect('carro-web')


@pasajero_requerido
def confirmar_compra(request):
    """Confirma la compra y convierte el carrito en una orden pagada."""
    if request.method != 'POST':
        return HttpResponseForbidden('La confirmación debe enviarse mediante POST.')
    carro_obj = get_object_or_404(Carro, usuario=request.user, activo=True)
    items = list(carro_obj.items.select_related('asiento__servicio').all())
    if not items:
        messages.error(request, 'Tu carro está vacío.')
        return redirect('carro-web')

    with transaction.atomic():
        asientos = list(
            Asiento.objects.select_for_update()
            .filter(pk__in=[item.asiento_id for item in items])
            .order_by('pk')
        )
        asientos_por_id = {asiento.pk: asiento for asiento in asientos}
        no_disponibles = [
            asiento.numero for asiento in asientos if asiento.ocupado
        ]
        if no_disponibles:
            messages.error(
                request,
                'No se pudo confirmar: los asientos '
                + ', '.join(str(numero) for numero in no_disponibles)
                + ' ya no están disponibles.',
            )
            return redirect('carro-web')

        total = sum(
            asientos_por_id[item.asiento_id].precio * item.cantidad
            for item in items
        )
        orden = Orden.objects.create(
            usuario=request.user,
            total=total,
            estado=Orden.Estado.PENDIENTE,
        )
        ItemOrden.objects.bulk_create([
            ItemOrden(
                orden=orden,
                servicio=item.asiento.servicio,
                asiento=asientos_por_id[item.asiento_id],
                precio_unitario=asientos_por_id[item.asiento_id].precio,
                nombre_pasajero=item.nombre_pasajero,
                documento_pasajero=item.documento_pasajero,
            )
            for item in items
        ])
        orden = cambiar_estado_orden(orden.pk, Orden.Estado.PAGADO)
        carro_obj.items.all().delete()

    messages.success(request, f'Compra #{orden.pk} confirmada. Tus pasajes ya están emitidos.')
    return redirect('orden-detalle-web', orden_id=orden.pk)


@pasajero_requerido
def mis_reservas(request):
    """Lista las compras del usuario autenticado con detalle de pasajes."""
    ordenes = (
        Orden.objects.filter(usuario=request.user)
        .prefetch_related(
            'items__servicio__ruta__origen__ciudad',
            'items__servicio__ruta__destino__ciudad',
            'items__servicio__bus',
            'items__asiento',
        )
        .order_by('-fecha')
    )
    return render(request, 'web/ordenes.html', {'ordenes': ordenes})


@pasajero_requerido
def ver_asientos_reserva(request, orden_id, item_id):
    """Redirige a la vista del servicio en modo solo lectura para revisar un boleto."""
    item = get_object_or_404(
        ItemOrden.objects.select_related('servicio'),
        pk=item_id,
        orden_id=orden_id,
        orden__usuario=request.user,
    )
    service_url = reverse('detalle-servicio', args=[item.servicio_id])
    return redirect(f'{service_url}?solo_lectura=1')


@pasajero_requerido
def cancelar_mis_pasajes(request, orden_id):
    """Cancela una orden del usuario autenticado y libera los asientos asociados."""
    if request.method != 'POST':
        return HttpResponseForbidden('La cancelación debe enviarse mediante POST.')
    orden = get_object_or_404(Orden, pk=orden_id, usuario=request.user)
    try:
        cambiar_estado_orden(orden.pk, Orden.Estado.CANCELADO)
    except (InvalidOrderTransition, SeatUnavailable) as error:
        messages.error(request, str(error))
    else:
        messages.success(
            request,
            f'La compra #{orden.pk} y sus pasajes fueron cancelados. '
            'Los asientos quedaron disponibles nuevamente.',
        )
    return redirect('orden-detalle-web', orden_id=orden.pk)


@login_required
def detalle_orden(request, orden_id):
    """Muestra el detalle completo de una orden y sus asientos comprados."""
    orden = get_object_or_404(
        Orden.objects.prefetch_related('items__servicio', 'items__asiento'),
        pk=orden_id,
    )
    if not request.user.is_admin() and orden.usuario_id != request.user.pk:
        return HttpResponseForbidden('No tienes permiso para consultar esta compra.')
    return render(request, 'web/orden_detalle.html', {
        'orden': orden,
        'estados': Orden.Estado.choices,
        'puede_cancelar': (
            not request.user.is_admin()
            and orden.estado in [Orden.Estado.PAGADO, Orden.Estado.PENDIENTE]
        ),
    })


RESOURCES = {
    'ciudades': {
        'model': Ciudad,
        'label': 'Ciudades',
        'fields': ['nombre'],
        'search_fields': ['nombre__icontains'],
    },
    'terminales': {
        'model': Terminal,
        'label': 'Terminales',
        'fields': ['nombre', 'ciudad'],
        'search_fields': ['nombre__icontains', 'ciudad__nombre__icontains'],
    },
    'rutas': {
        'model': Ruta,
        'label': 'Rutas',
        'fields': ['origen', 'destino', 'distancia_km'],
        'search_fields': [
            'origen__nombre__icontains',
            'origen__ciudad__nombre__icontains',
            'destino__nombre__icontains',
            'destino__ciudad__nombre__icontains',
        ],
    },
    'buses': {
        'model': Bus,
        'label': 'Buses',
        'fields': ['patente', 'marca', 'modelo', 'capacidad', 'cantidad_cama'],
        'search_fields': [
            'patente__icontains',
            'marca__icontains',
            'modelo__icontains',
        ],
    },
    'servicios': {
        'model': Servicio,
        'label': 'Servicios',
        'fields': [
            'ruta', 'bus', 'fecha_salida', 'hora_salida',
            'precio_base', 'precio_cama',
        ],
        'search_fields': [
            'ruta__origen__ciudad__nombre__icontains',
            'ruta__destino__ciudad__nombre__icontains',
            'bus__patente__icontains',
        ],
    },
}


class BusForm(forms.ModelForm):
    """Validates the bus capacity and its cama-seat allocation."""

    class Meta:
        model = Bus
        fields = RESOURCES['buses']['fields']

    def clean(self):
        cleaned_data = super().clean()
        capacidad = cleaned_data.get('capacidad')
        cantidad_cama = cleaned_data.get('cantidad_cama')
        if capacidad is not None and cantidad_cama is not None and cantidad_cama > capacidad:
            self.add_error('cantidad_cama', 'No puede superar la capacidad total del bus.')
        if (
            self.instance.pk
            and self.instance.servicios.exists()
            and capacidad != self.instance.capacidad
        ):
            self.add_error('capacidad', 'No puede cambiar la capacidad de un bus asignado a servicios.')
        if (
            self.instance.pk
            and self.instance.servicios.exists()
            and cantidad_cama != self.instance.cantidad_cama
        ):
            self.add_error('cantidad_cama', 'No puede cambiar los asientos cama de un bus asignado a servicios.')
        return cleaned_data


class ServicioForm(forms.ModelForm):
    """Captures a service's route, vehicle, schedule, and fare by seat type."""

    class Meta:
        model = Servicio
        fields = RESOURCES['servicios']['fields']
        widgets = {
            'fecha_salida': forms.DateInput(attrs={'type': 'date'}),
            'hora_salida': forms.TimeInput(attrs={'type': 'time'}),
            'precio_base': forms.NumberInput(attrs={'min': '0', 'step': '100'}),
            'precio_cama': forms.NumberInput(attrs={'min': '0', 'step': '100'}),
        }

    def clean_bus(self):
        bus = self.cleaned_data['bus']
        if (
            self.instance.pk
            and self.instance.bus_id != bus.pk
            and self.instance.asientos.exists()
        ):
            raise forms.ValidationError(
                'No puedes cambiar el bus después de asignar los asientos al servicio.'
            )
        return bus


def resource_or_404(key):
    """Resuelve un recurso de gestion o lanza una 404 si la seccion no existe."""
    if key not in RESOURCES:
        from django.http import Http404
        raise Http404('La sección solicitada no existe.')
    return RESOURCES[key]


@admin_requerido
def gestion_inicio(request):
    """Presenta el panel de administracion con metricas de la operacion del sistema."""
    recursos = [
        ('ciudades', 'Ciudades', Ciudad.objects.count(), 'Orígenes y destinos'),
        ('terminales', 'Terminales', Terminal.objects.count(), 'Puntos de embarque'),
        ('rutas', 'Rutas', Ruta.objects.count(), 'Conexiones entre terminales'),
        ('buses', 'Buses', Bus.objects.count(), 'Capacidad y asientos cama'),
        ('servicios', 'Viajes', Servicio.objects.count(), 'Horarios y tarifas'),
    ]
    return render(request, 'web/gestion_inicio.html', {
        'recursos': recursos,
        'ordenes_total': Orden.objects.count(),
        'pendientes_total': Orden.objects.filter(estado=Orden.Estado.PENDIENTE).count(),
    })


@admin_requerido
def gestion_lista(request, recurso):
    """Lista registros de administracion segun el recurso solicitado."""
    config = resource_or_404(recurso)
    queryset = config['model'].objects.all()
    if recurso == 'servicios':
        queryset = queryset.select_related(
            'ruta__origen__ciudad', 'ruta__destino__ciudad', 'bus'
        )
    elif recurso == 'terminales':
        queryset = queryset.select_related('ciudad')
    elif recurso == 'rutas':
        queryset = queryset.select_related(
            'origen__ciudad', 'destino__ciudad'
        )

    busqueda = request.GET.get('q', '').strip()
    if busqueda:
        filtros = Q()
        for campo in config['search_fields']:
            filtros |= Q(**{campo: busqueda})
        queryset = queryset.filter(filtros)

    return render(request, 'web/gestion_lista.html', {
        'objetos': queryset,
        'recurso': recurso,
        'etiqueta': config['label'],
        'busqueda': busqueda,
        'total_objetos': queryset.count(),
    })


@admin_requerido
def gestion_formulario(request, recurso, objeto_id=None):
    """Crea o edita un registro del panel de gestion de la operacion."""
    config = resource_or_404(recurso)
    instance = get_object_or_404(config['model'], pk=objeto_id) if objeto_id else None
    if recurso == 'buses':
        form_class = BusForm
    elif recurso == 'servicios':
        form_class = ServicioForm
    else:
        form_class = modelform_factory(config['model'], fields=config['fields'])
    form = form_class(request.POST or None, instance=instance)
    if request.method == 'POST' and form.is_valid():
        objeto = form.save()
        if recurso == 'servicios' and not objeto.asientos.exists():
            cantidad = objeto.bus.capacidad
            camas = objeto.bus.cantidad_cama
            Asiento.objects.bulk_create([
                Asiento(
                    servicio=objeto,
                    numero=numero,
                    tipo=(
                        Asiento.Tipo.CAMA
                        if numero <= camas
                        else Asiento.Tipo.SEMICAMA
                    ),
                )
                for numero in range(1, cantidad + 1)
            ])
        messages.success(
            request,
            f'{objeto._meta.verbose_name.capitalize()} guardado correctamente.',
        )
        return redirect('gestion-lista', recurso=recurso)
    return render(request, 'web/gestion_formulario.html', {
        'form': form,
        'recurso': recurso,
        'etiqueta': config['label'],
        'objeto': instance,
    })


@admin_requerido
def gestion_eliminar(request, recurso, objeto_id):
    """Elimina un registro del catalogo y protege operaciones con boletos asociados."""
    config = resource_or_404(recurso)
    objeto = get_object_or_404(config['model'], pk=objeto_id)
    if request.method == 'POST':
        try:
            objeto.delete()
        except ProtectedError:
            messages.error(
                request,
                'No se puede eliminar este registro porque tiene boletos asociados.',
            )
            return redirect('gestion-lista', recurso=recurso)
        messages.success(request, f'Registro eliminado de {config["label"].lower()}.')
        return redirect('gestion-lista', recurso=recurso)
    return render(request, 'web/gestion_eliminar.html', {
        'objeto': objeto,
        'recurso': recurso,
        'etiqueta': config['label'],
    })


@admin_requerido
def gestion_ordenes(request):
    """Lista las ordenes del negocio con su estado y metadatos de usuario."""
    ordenes = Orden.objects.select_related('usuario').prefetch_related(
        'items'
    ).order_by('-fecha')
    return render(request, 'web/gestion_ordenes.html', {'ordenes': ordenes})


@admin_requerido
def gestion_cambiar_estado(request, orden_id):
    """Actualiza el estado de una orden desde el panel administrativo."""
    if request.method != 'POST':
        return HttpResponseForbidden('El cambio de estado debe enviarse mediante POST.')
    estado = request.POST.get('estado', '')
    estados_validos = dict(Orden.Estado.choices)
    if estado not in estados_validos:
        messages.error(request, 'El estado seleccionado no es válido.')
    else:
        try:
            cambiar_estado_orden(orden_id, estado)
        except Orden.DoesNotExist:
            messages.error(request, 'La orden solicitada no existe.')
            return redirect('gestion-ordenes')
        except (InvalidOrderTransition, SeatUnavailable) as error:
            messages.error(request, str(error))
        else:
            if estado == Orden.Estado.CANCELADO:
                messages.success(
                    request,
                    'La compra fue cancelada y sus pasajes quedaron disponibles nuevamente.',
                )
            else:
                messages.success(request, 'El estado de la orden fue actualizado.')
    return redirect('orden-detalle-web', orden_id=orden_id)
