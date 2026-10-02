from datetime import date, time, timedelta
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from rest_framework_simplejwt.tokens import AccessToken

from carrito.models import Carro
from transporte.models import Asiento, Bus, Ciudad, Ruta, Servicio, Terminal
from ventas.models import Orden


Usuario = get_user_model()


class BusReservationTemplateTests(TestCase):
    """Covers the passenger and administrator journeys rendered by Django templates."""

    @classmethod
    def setUpTestData(cls):
        cls.pasajero = Usuario.objects.create_user(
            username='viajero',
            password='Clave-segura-2026',
            rol=Usuario.Rol.PASAJERO,
        )
        cls.administrador = Usuario.objects.create_user(
            username='gestor',
            password='Clave-segura-2026',
            rol=Usuario.Rol.ADMINISTRADOR,
        )
        origen = Ciudad.objects.create(nombre='Santiago')
        destino = Ciudad.objects.create(nombre='Temuco')
        terminal_origen = Terminal.objects.create(nombre='Terminal Central', ciudad=origen)
        terminal_destino = Terminal.objects.create(nombre='Terminal Sur', ciudad=destino)
        ruta = Ruta.objects.create(
            origen=terminal_origen,
            destino=terminal_destino,
            distancia_km=670,
        )
        bus = Bus.objects.create(
            patente='TEST11',
            marca='Volvo',
            modelo='Prueba',
            capacidad=4,
            cantidad_cama=1,
        )
        cls.servicio = Servicio.objects.create(
            ruta=ruta,
            bus=bus,
            fecha_salida=date.today() + timedelta(days=2),
            hora_salida=time(9, 0),
            precio_base=20000,
            precio_cama=30000,
        )
        cls.asiento_cama = Asiento.objects.create(
            servicio=cls.servicio,
            numero=1,
            tipo=Asiento.Tipo.CAMA,
        )
        Asiento.objects.bulk_create([
            Asiento(servicio=cls.servicio, numero=numero)
            for numero in range(2, 5)
        ])

    def test_home_and_search_render_from_database(self):
        home = self.client.get(reverse('home'))
        self.assertEqual(home.status_code, 200)
        self.assertContains(home, 'BusGo')
        self.assertContains(home, 'Temuco')

        results = self.client.get(reverse('buscar-viajes'), {
            'origen': 'Santiago',
            'destino': 'Temuco',
            'pasajeros': '2',
        })
        self.assertEqual(results.status_code, 200)
        self.assertContains(results, 'Elegir asientos')
        self.assertContains(results, 'Volvo')
        self.assertContains(results, 'TEST11')
        self.assertContains(results, '4 asientos')

    def test_unknown_web_path_renders_not_found_page_and_unknown_api_remains_404(self):
        not_found = self.client.get('/ded')
        self.assertEqual(not_found.status_code, 404)
        self.assertContains(not_found, 'Página no encontrada', status_code=404)
        self.assertContains(not_found, '>Volver</a>', status_code=404)
        self.assertEqual(self.client.get('/api/no-such-endpoint/').status_code, 404)

    def test_admin_uses_template_portal_and_passenger_cannot_access_it(self):
        denied = self.client.get(reverse('gestion-inicio'))
        self.assertEqual(denied.status_code, 302)

        self.client.force_login(self.pasajero)
        denied = self.client.get(reverse('gestion-inicio'))
        self.assertEqual(denied.status_code, 403)

        self.client.force_login(self.administrador)
        dashboard = self.client.get(reverse('gestion-inicio'))
        self.assertEqual(dashboard.status_code, 200)
        self.assertContains(dashboard, 'Panel de administrador')
        self.assertContains(dashboard, 'Agregar')
        self.assertEqual(self.client.get('/admin/').status_code, 302)

    def test_admin_can_create_fleet_records_with_template_form(self):
        self.client.force_login(self.administrador)
        form = self.client.get(reverse('gestion-nuevo', args=['ciudades']))
        self.assertEqual(form.status_code, 200)
        response = self.client.post(
            reverse('gestion-nuevo', args=['ciudades']),
            {'nombre': 'Valdivia'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Ciudad.objects.filter(nombre='Valdivia').exists())

    def test_passenger_selects_a_specific_seat_from_interactive_seat_map(self):
        self.client.force_login(self.pasajero)
        asiento_elegido = self.servicio.asientos.get(numero=3)

        page = self.client.get(reverse('detalle-servicio', args=[self.servicio.pk]))
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'name="asientos_ids"')
        self.assertContains(page, f'value="{asiento_elegido.pk}"')
        self.assertContains(page, 'class="seat-row"')
        self.assertContains(page, 'class="seat-aisle"')
        self.assertContains(page, 'Seleccionado')
        self.assertContains(page, 'Añadir pasajes seleccionados al carro')
        self.assertContains(page, 'data-rut-input')
        self.assertContains(page, 'Nombre completo de quien compra')
        self.assertContains(page, 'data-rut-feedback')
        self.assertContains(page, 'Bus:')
        self.assertContains(page, 'TEST11')
        self.assertNotContains(page, 'Nombre de cada pasajero')

        response = self.client.post(
            reverse('detalle-servicio', args=[self.servicio.pk]),
            {
                'asientos_ids': [asiento_elegido.pk],
                'nombre_comprador': 'Pasajera Asiento Tres',
                'documento_pasajero': '11.111.111-1',
            },
        )
        self.assertRedirects(response, reverse('carro-web'))
        item = self.pasajero.carro.items.get()
        self.assertEqual(item.asiento_id, asiento_elegido.pk)
        self.assertEqual(item.asiento.numero, 3)

    def test_demo_data_includes_more_destinations_and_route_search_options(self):
        call_command('cargar_datos_prueba', stdout=StringIO())

        self.assertEqual(Ciudad.objects.count(), 8)
        self.assertTrue(Ruta.objects.filter(
            origen__ciudad__nombre='Santiago',
            destino__ciudad__nombre='Valparaíso',
        ).exists())
        self.assertTrue(Servicio.objects.filter(
            ruta__origen__ciudad__nombre='Santiago',
            ruta__destino__ciudad__nombre='La Serena',
        ).exists())
        results = self.client.get(reverse('buscar-viajes'))
        self.assertContains(results, 'Valdivia')

    def test_admin_can_create_and_manage_related_city_terminal_route_and_service(self):
        self.client.force_login(self.administrador)
        self.client.post(
            reverse('gestion-nuevo', args=['ciudades']),
            {'nombre': 'Vallenar'},
        )
        origen = Ciudad.objects.get(nombre='Vallenar')
        self.client.post(
            reverse('gestion-nuevo', args=['ciudades']),
            {'nombre': 'Puerto Varas'},
        )
        destino = Ciudad.objects.get(nombre='Puerto Varas')

        self.client.post(
            reverse('gestion-nuevo', args=['terminales']),
            {'nombre': 'Terminal Vallenar', 'ciudad': origen.pk},
        )
        terminal_origen = Terminal.objects.get(nombre='Terminal Vallenar')
        self.client.post(
            reverse('gestion-nuevo', args=['terminales']),
            {'nombre': 'Terminal Puerto Varas', 'ciudad': destino.pk},
        )
        terminal_destino = Terminal.objects.get(nombre='Terminal Puerto Varas')

        ruta_form = self.client.get(reverse('gestion-nuevo', args=['rutas']))
        self.assertContains(ruta_form, 'Terminal Vallenar')
        self.assertContains(ruta_form, 'Terminal Puerto Varas')
        self.client.post(
            reverse('gestion-nuevo', args=['rutas']),
            {
                'origen': terminal_origen.pk,
                'destino': terminal_destino.pk,
                'distancia_km': 820,
            },
        )
        ruta = Ruta.objects.get(origen=terminal_origen, destino=terminal_destino)

        self.client.post(
            reverse('gestion-nuevo', args=['buses']),
            {
                'patente': 'CRUD22',
                'marca': 'Volvo',
                'modelo': 'Intercity',
                'capacidad': 4,
                'cantidad_cama': 1,
            },
        )
        bus = Bus.objects.get(patente='CRUD22')
        servicio_form = self.client.get(reverse('gestion-nuevo', args=['servicios']))
        self.assertContains(servicio_form, 'Vallenar')
        self.assertContains(servicio_form, 'Puerto Varas')
        self.client.post(
            reverse('gestion-nuevo', args=['servicios']),
            {
                'ruta': ruta.pk,
                'bus': bus.pk,
                'fecha_salida': (date.today() + timedelta(days=8)).isoformat(),
                'hora_salida': '07:45',
                'precio_base': '18000',
                'precio_cama': '27000',
            },
        )
        servicio = Servicio.objects.get(ruta=ruta, bus=bus)
        self.assertEqual(servicio.asientos.count(), 4)

        self.client.post(
            reverse('gestion-editar', args=['ciudades', destino.pk]),
            {'nombre': 'Puerto Varas Nuevo'},
        )
        self.client.post(
            reverse('gestion-editar', args=['terminales', terminal_destino.pk]),
            {'nombre': 'Terminal Puerto Varas Nuevo', 'ciudad': destino.pk},
        )
        self.client.post(
            reverse('gestion-editar', args=['rutas', ruta.pk]),
            {
                'origen': terminal_origen.pk,
                'destino': terminal_destino.pk,
                'distancia_km': 830,
            },
        )
        self.client.post(
            reverse('gestion-editar', args=['buses', bus.pk]),
            {
                'patente': 'CRUD22',
                'marca': 'Volvo',
                'modelo': 'Intercity Plus',
                'capacidad': 4,
                'cantidad_cama': 1,
            },
        )
        self.client.post(
            reverse('gestion-editar', args=['servicios', servicio.pk]),
            {
                'ruta': ruta.pk,
                'bus': bus.pk,
                'fecha_salida': (date.today() + timedelta(days=9)).isoformat(),
                'hora_salida': '08:15',
                'precio_base': '19000',
                'precio_cama': '28000',
            },
        )
        self.assertEqual(Ciudad.objects.get(pk=destino.pk).nombre, 'Puerto Varas Nuevo')
        self.assertEqual(Ruta.objects.get(pk=ruta.pk).distancia_km, 830)
        self.assertEqual(Bus.objects.get(pk=bus.pk).modelo, 'Intercity Plus')
        servicio.refresh_from_db()
        self.assertEqual(servicio.precio_base, 19000)
        self.assertEqual(servicio.precio_cama, 28000)
        self.assertEqual(servicio.asientos.get(numero=1).precio, 28000)
        self.assertEqual(servicio.asientos.get(numero=2).precio, 19000)
        service_list = self.client.get(reverse('gestion-lista', args=['servicios']))
        self.assertContains(service_list, 'Cambiar precios')
        edit_service_form = self.client.get(
            reverse('gestion-editar', args=['servicios', servicio.pk])
        )
        self.assertContains(edit_service_form, 'tarifas semicama y cama')

        search = self.client.get(reverse('gestion-lista', args=['rutas']), {'q': 'Puerto Varas Nuevo'})
        self.assertContains(search, 'Terminal Puerto Varas Nuevo')
        for recurso, objeto in [
            ('servicios', servicio),
            ('buses', bus),
            ('rutas', ruta),
            ('terminales', terminal_destino),
            ('terminales', terminal_origen),
            ('ciudades', destino),
            ('ciudades', origen),
        ]:
            response = self.client.post(
                reverse('gestion-eliminar', args=[recurso, objeto.pk]),
            )
            self.assertEqual(response.status_code, 302)

    def test_admin_service_form_assigns_seat_types_from_bus_configuration(self):
        self.client.force_login(self.administrador)
        response = self.client.post(
            reverse('gestion-nuevo', args=['servicios']),
            {
                'ruta': self.servicio.ruta_id,
                'bus': self.servicio.bus_id,
                'fecha_salida': (date.today() + timedelta(days=10)).isoformat(),
                'hora_salida': '11:30',
                'precio_base': '21000',
                'precio_cama': '31000',
            },
        )
        self.assertEqual(response.status_code, 302)
        nuevo_servicio = Servicio.objects.get(
            fecha_salida=date.today() + timedelta(days=10),
            hora_salida=time(11, 30),
        )
        self.assertEqual(nuevo_servicio.asientos.count(), 4)
        self.assertEqual(
            nuevo_servicio.asientos.filter(tipo=Asiento.Tipo.CAMA).count(),
            1,
        )

    def test_passenger_can_register_and_log_in_through_templates(self):
        register = self.client.get(reverse('registro-web'))
        self.assertEqual(register.status_code, 200)
        response = self.client.post(reverse('registro-web'), {
            'username': 'nueva_viajera',
            'first_name': 'Nueva',
            'last_name': 'Viajera',
            'email': 'viajera@example.test',
            'password1': 'Ruta-Segura!2026',
            'password2': 'Ruta-Segura!2026',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Usuario.objects.filter(username='nueva_viajera').exists())

    def test_passenger_cart_survives_logout_and_checkout_pays_and_issues_ticket(self):
        self.client.force_login(self.pasajero)
        response = self.client.post(
            reverse('detalle-servicio', args=[self.servicio.pk]),
            {
                'asientos_ids': [self.asiento_cama.pk],
                'nombre_comprador': 'Camila Prueba',
                'documento_pasajero': '11.111.111-1',
            },
        )
        self.assertEqual(response.status_code, 302)

        self.client.post(reverse('logout-web'))
        self.client.force_login(self.pasajero)
        cart = self.client.get(reverse('carro-web'))
        self.assertContains(cart, 'Camila Prueba')
        self.assertContains(cart, '11.111.111-1')

        self.client.post(reverse('carro-confirmar-web'))
        orden = Orden.objects.get(usuario=self.pasajero)
        item = orden.items.get()
        self.assertEqual(orden.estado, Orden.Estado.PAGADO)
        self.assertEqual(orden.total, 30000)
        self.asiento_cama.refresh_from_db()
        self.assertTrue(self.asiento_cama.ocupado)
        self.assertEqual(item.nombre_pasajero, 'Camila Prueba')
        self.assertTrue(item.codigo_boleto)

        self.client.force_login(self.administrador)
        ticket = self.client.get(reverse('orden-detalle-web', args=[orden.pk]))
        self.assertContains(ticket, str(item.codigo_boleto))
        jwt_response = self.client.post(
            '/api/login/',
            data={
                'username': self.pasajero.username,
                'password': 'Clave-segura-2026',
            },
        )
        self.assertEqual(jwt_response.status_code, 200)
        boletos = self.client.get(
            '/api/mis-boletos/',
            HTTP_AUTHORIZATION=f"Bearer {jwt_response.json()['access']}",
        )
        self.assertEqual(boletos.status_code, 200)
        self.assertEqual(
            boletos.json()['results'][0]['codigo_boleto'],
            str(item.codigo_boleto),
        )

        cancelled = self.client.post(
            reverse('gestion-orden-cambiar-estado', args=[orden.pk]),
            {'estado': Orden.Estado.CANCELADO},
        )
        self.assertEqual(cancelled.status_code, 302)
        self.asiento_cama.refresh_from_db()
        self.assertFalse(self.asiento_cama.ocupado)

    def test_passenger_can_select_multiple_seats_and_invalid_rut_is_rejected(self):
        self.client.force_login(self.pasajero)
        seats = list(self.servicio.asientos.filter(numero__in=[2, 3]).order_by('numero'))
        response = self.client.post(
            reverse('detalle-servicio', args=[self.servicio.pk]),
            {
                'asientos_ids': [seat.pk for seat in seats],
                'nombre_comprador': 'Comprador Prueba',
                'documento_pasajero': '12.345.678-9',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'RUT no es')
        self.assertFalse(hasattr(self.pasajero, 'carro'))

        response = self.client.post(
            reverse('detalle-servicio', args=[self.servicio.pk]),
            {
                'asientos_ids': [seat.pk for seat in seats],
                'nombre_comprador': 'Comprador Prueba',
                'documento_pasajero': '11.111.111-1',
            },
        )
        self.assertRedirects(response, reverse('carro-web'))
        self.assertEqual(Carro.objects.get(usuario=self.pasajero).items.count(), 2)

        self.client.post(reverse('carro-confirmar-web'))
        orden = Orden.objects.get(usuario=self.pasajero)
        self.assertEqual(orden.estado, Orden.Estado.PAGADO)
        self.assertEqual(orden.items.count(), 2)
        self.assertEqual(
            set(orden.items.values_list('documento_pasajero', flat=True)),
            {'11.111.111-1'},
        )
        self.assertEqual(
            set(orden.items.values_list('asiento__numero', flat=True)),
            {2, 3},
        )
        self.assertEqual(
            Asiento.objects.filter(servicio=self.servicio, ocupado=True).count(),
            2,
        )

    def test_passenger_cannot_select_seat_beyond_bus_capacity(self):
        extra_seat = Asiento.objects.create(
            servicio=self.servicio,
            numero=self.servicio.bus.capacidad + 1,
        )
        self.client.force_login(self.pasajero)
        response = self.client.post(
            reverse('detalle-servicio', args=[self.servicio.pk]),
            {
                'asientos_ids': [extra_seat.pk],
                'nombre_comprador': 'Comprador Prueba',
                'documento_pasajero': '11.111.111-1',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'supera los asientos disponibles del bus')
        self.assertFalse(hasattr(self.pasajero, 'carro'))

    def test_admin_can_cancel_purchase_from_sales_list_and_release_all_seats(self):
        seats = list(self.servicio.asientos.filter(numero__in=[2, 3]).order_by('numero'))
        self.client.force_login(self.pasajero)
        add_response = self.client.post(
            reverse('detalle-servicio', args=[self.servicio.pk]),
            {
                'asientos_ids': [seat.pk for seat in seats],
                'nombre_comprador': 'Comprador Cancelacion',
                'documento_pasajero': '11.111.111-1',
            },
        )
        self.assertRedirects(add_response, reverse('carro-web'))
        self.client.post(reverse('carro-confirmar-web'))
        orden = Orden.objects.get(usuario=self.pasajero)
        self.assertEqual(orden.estado, Orden.Estado.PAGADO)
        self.assertEqual(
            Asiento.objects.filter(pk__in=[seat.pk for seat in seats], ocupado=True).count(),
            2,
        )

        self.client.force_login(self.administrador)
        sales = self.client.get(reverse('gestion-ordenes'))
        self.assertContains(sales, 'Cancelar')
        self.assertContains(sales, 'Comprador Cancelacion')
        cancelled = self.client.post(
            reverse('gestion-orden-cambiar-estado', args=[orden.pk]),
            {'estado': Orden.Estado.CANCELADO},
        )
        self.assertRedirects(cancelled, reverse('orden-detalle-web', args=[orden.pk]))

        orden.refresh_from_db()
        self.assertEqual(orden.estado, Orden.Estado.CANCELADO)
        self.assertEqual(
            Asiento.objects.filter(pk__in=[seat.pk for seat in seats], ocupado=True).count(),
            0,
        )
        self.assertEqual(
            Asiento.objects.filter(pk__in=[seat.pk for seat in seats], ocupado=False).count(),
            2,
        )

    def test_buyer_can_cancel_own_purchase_and_release_all_seats(self):
        seats = list(self.servicio.asientos.filter(numero__in=[2, 3]).order_by('numero'))
        self.client.force_login(self.pasajero)
        self.client.post(
            reverse('detalle-servicio', args=[self.servicio.pk]),
            {
                'asientos_ids': [seat.pk for seat in seats],
                'nombre_comprador': 'Comprador Cancelacion',
                'documento_pasajero': '11.111.111-1',
            },
        )
        self.client.post(reverse('carro-confirmar-web'))
        orden = Orden.objects.get(usuario=self.pasajero)
        self.assertEqual(orden.estado, Orden.Estado.PAGADO)
        self.assertContains(
            self.client.get(reverse('orden-detalle-web', args=[orden.pk])),
            'Cancelar compra',
        )

        response = self.client.post(
            reverse('mis-pasajes-cancelar-web', args=[orden.pk])
        )
        self.assertRedirects(response, reverse('orden-detalle-web', args=[orden.pk]))
        orden.refresh_from_db()
        self.assertEqual(orden.estado, Orden.Estado.CANCELADO)
        self.assertEqual(
            Asiento.objects.filter(pk__in=[seat.pk for seat in seats], ocupado=False).count(),
            2,
        )

    def test_buyer_cannot_cancel_another_users_purchase(self):
        another_buyer = Usuario.objects.create_user(
            username='otro_comprador',
            password='Clave-segura-2026',
            rol=Usuario.Rol.PASAJERO,
        )
        orden = Orden.objects.create(
            usuario=another_buyer,
            total=20000,
            estado=Orden.Estado.PAGADO,
        )
        seat = self.servicio.asientos.get(numero=2)
        seat.ocupado = True
        seat.save(update_fields=['ocupado'])
        orden.items.create(
            servicio=self.servicio,
            asiento=seat,
            precio_unitario=20000,
        )
        self.client.force_login(self.pasajero)

        response = self.client.post(
            reverse('mis-pasajes-cancelar-web', args=[orden.pk])
        )
        self.assertEqual(response.status_code, 404)
        orden.refresh_from_db()
        seat.refresh_from_db()
        self.assertEqual(orden.estado, Orden.Estado.PAGADO)
        self.assertTrue(seat.ocupado)

    def test_public_api_exposes_service_search_and_assigned_seats(self):
        search = self.client.get('/api/servicios/buscar/')
        self.assertEqual(search.status_code, 200)
        seats = self.client.get(f'/api/servicios/{self.servicio.pk}/asientos/')
        self.assertEqual(seats.status_code, 200)
        self.assertEqual(len(seats.json()), 4)

        docs = self.client.get('/api/docs/')
        self.assertEqual(docs.status_code, 200)
        schema = self.client.get('/api/schema/')
        self.assertEqual(schema.status_code, 200)

    def test_jwt_contains_role_and_mis_boletos_route_is_protected(self):
        response = self.client.post(
            '/api/login/',
            data={
                'username': self.pasajero.username,
                'password': 'Clave-segura-2026',
            },
        )
        self.assertEqual(response.status_code, 200)
        access = response.json()['access']
        self.assertEqual(AccessToken(access)['rol'], Usuario.Rol.PASAJERO)

        protected = self.client.get('/api/mis-boletos/')
        self.assertIn(protected.status_code, (401, 403))

        logout_response = self.client.post('/api/login/logout/', {
            'refresh': response.json()['refresh'],
        })
        self.assertEqual(logout_response.status_code, 200)
