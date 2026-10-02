"""
Comando para cargar datos de prueba iniciales.

Crea:
- Usuarios: admin, pasajero
- Ciudades: ocho destinos de Chile
- Terminales: un terminal de prueba por ciudad
- Buses: Bus 001, Bus 002
- Servicios: Santiago - Temuco

Uso: python manage.py cargar_datos_prueba
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from transporte.models import Ciudad, Terminal, Ruta, Bus, Servicio, Asiento

Usuario = get_user_model()


class Command(BaseCommand):
    help = 'Carga datos de prueba iniciales para el sistema de reservas de bus'
    
    def handle(self, *args, **options):
        self.stdout.write('Cargando datos de prueba...')
        
        # 1. Crear grupos de roles
        self.crear_grupos()
        
        # 2. Crear usuarios
        self.crear_usuarios()
        
        # 3. Crear ciudades
        ciudades = self.crear_ciudades()
        
        # 4. Crear terminales
        terminales = self.crear_terminales(ciudades)
        
        # 5. Crear rutas
        rutas = self.crear_rutas(terminales)
        
        # 6. Crear buses
        buses = self.crear_buses()
        
        # 7. Crear servicios y asientos
        self.crear_servicios_y_asientos(rutas, buses)
        
        self.stdout.write(
            self.style.SUCCESS('Datos de prueba cargados correctamente!')
        )
        self.stdout.write('')
        self.stdout.write('Usuarios creados:')
        self.stdout.write('  - admin / admin123 (ADMINISTRADOR)')
        self.stdout.write('  - pasajero / pasajero123 (PASAJERO)')
    
    def crear_grupos(self):
        """Crea los grupos de roles."""
        Group.objects.get_or_create(name='PASAJERO')
        Group.objects.get_or_create(name='ADMINISTRADOR')
        self.stdout.write('  OK Grupos creados')
    
    def crear_usuarios(self):
        """Crea usuarios de prueba."""
        # Admin
        admin, created = Usuario.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@busreservas.cl',
                'first_name': 'Admin',
                'last_name': 'Sistema',
                'rol': Usuario.Rol.ADMINISTRADOR,
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            admin.groups.add(Group.objects.get(name='ADMINISTRADOR'))
        self.stdout.write('  OK Usuario admin creado')
        
        # Pasajero
        pasajero, created = Usuario.objects.get_or_create(
            username='pasajero',
            defaults={
                'email': 'pasajero@busreservas.cl',
                'first_name': 'Juan',
                'last_name': 'Pérez',
                'rol': Usuario.Rol.PASAJERO,
            }
        )
        if created:
            pasajero.set_password('pasajero123')
            pasajero.save()
            pasajero.groups.add(Group.objects.get(name='PASAJERO'))
        self.stdout.write('  OK Usuario pasajero creado')
    
    def crear_ciudades(self):
        """Crea ciudades de prueba."""
        ciudades_data = [
            {'nombre': 'Santiago'},
            {'nombre': 'Temuco'},
            {'nombre': 'Concepción'},
            {'nombre': 'Valparaíso'},
            {'nombre': 'La Serena'},
            {'nombre': 'Chillán'},
            {'nombre': 'Valdivia'},
            {'nombre': 'Puerto Montt'},
        ]
        
        ciudades = {}
        for data in ciudades_data:
            ciudad, _ = Ciudad.objects.get_or_create(**data)
            ciudades[ciudad.nombre] = ciudad
        
        self.stdout.write('  OK Ciudades creadas')
        return ciudades
    
    def crear_terminales(self, ciudades):
        """Crea terminales de prueba."""
        terminales_data = [
            {'nombre': 'Terminal Santiago', 'ciudad': ciudades['Santiago']},
            {'nombre': 'Terminal Temuco', 'ciudad': ciudades['Temuco']},
            {'nombre': 'Terminal Concepción', 'ciudad': ciudades['Concepción']},
            {'nombre': 'Terminal Valparaíso', 'ciudad': ciudades['Valparaíso']},
            {'nombre': 'Terminal La Serena', 'ciudad': ciudades['La Serena']},
            {'nombre': 'Terminal Chillán', 'ciudad': ciudades['Chillán']},
            {'nombre': 'Terminal Valdivia', 'ciudad': ciudades['Valdivia']},
            {'nombre': 'Terminal Puerto Montt', 'ciudad': ciudades['Puerto Montt']},
        ]
        
        terminales = {}
        for data in terminales_data:
            terminal, _ = Terminal.objects.get_or_create(**data)
            terminales[terminal.nombre] = terminal
        
        self.stdout.write('  OK Terminales creadas')
        return terminales
    
    def crear_rutas(self, terminales):
        """Crea rutas de prueba."""
        rutas_data = [
            {'origen': terminales['Terminal Santiago'], 'destino': terminales['Terminal Temuco'], 'distancia_km': 670},
            {'origen': terminales['Terminal Santiago'], 'destino': terminales['Terminal Concepción'], 'distancia_km': 510},
            {'origen': terminales['Terminal Temuco'], 'destino': terminales['Terminal Concepción'], 'distancia_km': 320},
            {'origen': terminales['Terminal Santiago'], 'destino': terminales['Terminal Valparaíso'], 'distancia_km': 120},
            {'origen': terminales['Terminal Santiago'], 'destino': terminales['Terminal La Serena'], 'distancia_km': 470},
            {'origen': terminales['Terminal Santiago'], 'destino': terminales['Terminal Chillán'], 'distancia_km': 400},
            {'origen': terminales['Terminal Concepción'], 'destino': terminales['Terminal Chillán'], 'distancia_km': 110},
            {'origen': terminales['Terminal Temuco'], 'destino': terminales['Terminal Valdivia'], 'distancia_km': 170},
            {'origen': terminales['Terminal Valdivia'], 'destino': terminales['Terminal Puerto Montt'], 'distancia_km': 210},
            {'origen': terminales['Terminal Temuco'], 'destino': terminales['Terminal Puerto Montt'], 'distancia_km': 290},
            {'origen': terminales['Terminal Santiago'], 'destino': terminales['Terminal Puerto Montt'], 'distancia_km': 1030},
        ]
        
        rutas = {}
        for data in rutas_data:
            ruta, _ = Ruta.objects.get_or_create(
                origen=data['origen'],
                destino=data['destino'],
                defaults={'distancia_km': data['distancia_km']}
            )
            key = f"{ruta.origen.nombre} → {ruta.destino.nombre}"
            rutas[key] = ruta
        
        self.stdout.write('  OK Rutas creadas')
        return rutas
    
    def crear_buses(self):
        """Crea buses de prueba."""
        buses_data = [
            {'patente': 'BBBB11', 'marca': 'Mercedes Benz', 'modelo': 'O500', 'capacidad': 30, 'cantidad_cama': 6},
            {'patente': 'CCCC22', 'marca': 'Volvo', 'modelo': 'B8R', 'capacidad': 40, 'cantidad_cama': 8},
            {'patente': 'DDDD33', 'marca': 'Scania', 'modelo': 'K320', 'capacidad': 35, 'cantidad_cama': 6},
        ]
        
        buses = {}
        for data in buses_data:
            bus, created = Bus.objects.get_or_create(
                patente=data['patente'],
                defaults=data,
            )
            if not created and bus.cantidad_cama != data['cantidad_cama']:
                bus.cantidad_cama = data['cantidad_cama']
                bus.save(update_fields=['cantidad_cama'])
            buses[bus.patente] = bus
        
        self.stdout.write('  OK Buses creados')
        return buses
    
    def crear_servicios_y_asientos(self, rutas, buses):
        """Crea servicios y sus asientos."""
        from datetime import date, timedelta
        
        # Servicios de prueba
        ruta_st_temuco = rutas.get('Terminal Santiago → Terminal Temuco')
        ruta_st_conce = rutas.get('Terminal Santiago → Terminal Concepción')
        ruta_temuco_conce = rutas.get('Terminal Temuco → Terminal Concepción')
        ruta_st_valparaiso = rutas.get('Terminal Santiago → Terminal Valparaíso')
        ruta_st_laserena = rutas.get('Terminal Santiago → Terminal La Serena')
        ruta_st_chillan = rutas.get('Terminal Santiago → Terminal Chillán')
        ruta_conce_chillan = rutas.get('Terminal Concepción → Terminal Chillán')
        ruta_temuco_valdivia = rutas.get('Terminal Temuco → Terminal Valdivia')
        ruta_valdivia_puerto_montt = rutas.get('Terminal Valdivia → Terminal Puerto Montt')
        ruta_temuco_puerto_montt = rutas.get('Terminal Temuco → Terminal Puerto Montt')
        ruta_st_puerto_montt = rutas.get('Terminal Santiago → Terminal Puerto Montt')
        
        bus_bbbb11 = buses.get('BBBB11')
        bus_cccc22 = buses.get('CCCC22')
        bus_dddd33 = buses.get('DDDD33')
        
        hoy = date.today()
        
        servicios_data = [
            # Santiago - Temuco
            {
                'ruta': ruta_st_temuco,
                'bus': bus_bbbb11,
                'fecha_salida': hoy + timedelta(days=1),
                'hora_salida': '08:00',
                'precio_base': 25000,
                'precio_cama': 35000,
            },
            {
                'ruta': ruta_st_temuco,
                'bus': bus_cccc22,
                'fecha_salida': hoy + timedelta(days=1),
                'hora_salida': '14:00',
                'precio_base': 28000,
                'precio_cama': 38000,
            },
            {
                'ruta': ruta_st_temuco,
                'bus': bus_dddd33,
                'fecha_salida': hoy + timedelta(days=2),
                'hora_salida': '10:00',
                'precio_base': 26000,
                'precio_cama': 36000,
            },
            # Santiago - Concepción
            {
                'ruta': ruta_st_conce,
                'bus': bus_bbbb11,
                'fecha_salida': hoy + timedelta(days=1),
                'hora_salida': '09:00',
                'precio_base': 20000,
                'precio_cama': 30000,
            },
            # Temuco - Concepción
            {
                'ruta': ruta_temuco_conce,
                'bus': bus_cccc22,
                'fecha_salida': hoy + timedelta(days=2),
                'hora_salida': '16:00',
                'precio_base': 15000,
                'precio_cama': 25000,
            },
            {
                'ruta': ruta_st_valparaiso,
                'bus': bus_dddd33,
                'fecha_salida': hoy + timedelta(days=2),
                'hora_salida': '07:30',
                'precio_base': 12000,
                'precio_cama': 20000,
            },
            {
                'ruta': ruta_st_laserena,
                'bus': bus_cccc22,
                'fecha_salida': hoy + timedelta(days=2),
                'hora_salida': '20:00',
                'precio_base': 24000,
                'precio_cama': 34000,
            },
            {
                'ruta': ruta_st_chillan,
                'bus': bus_bbbb11,
                'fecha_salida': hoy + timedelta(days=3),
                'hora_salida': '08:30',
                'precio_base': 18000,
                'precio_cama': 28000,
            },
            {
                'ruta': ruta_conce_chillan,
                'bus': bus_dddd33,
                'fecha_salida': hoy + timedelta(days=3),
                'hora_salida': '12:00',
                'precio_base': 9000,
                'precio_cama': 15000,
            },
            {
                'ruta': ruta_temuco_valdivia,
                'bus': bus_cccc22,
                'fecha_salida': hoy + timedelta(days=4),
                'hora_salida': '10:30',
                'precio_base': 11000,
                'precio_cama': 18000,
            },
            {
                'ruta': ruta_valdivia_puerto_montt,
                'bus': bus_bbbb11,
                'fecha_salida': hoy + timedelta(days=4),
                'hora_salida': '15:00',
                'precio_base': 13000,
                'precio_cama': 21000,
            },
            {
                'ruta': ruta_temuco_puerto_montt,
                'bus': bus_dddd33,
                'fecha_salida': hoy + timedelta(days=5),
                'hora_salida': '09:00',
                'precio_base': 17000,
                'precio_cama': 27000,
            },
            {
                'ruta': ruta_st_puerto_montt,
                'bus': bus_cccc22,
                'fecha_salida': hoy + timedelta(days=5),
                'hora_salida': '18:00',
                'precio_base': 32000,
                'precio_cama': 44000,
            },
        ]
        
        for data in servicios_data:
            servicio, created = Servicio.objects.get_or_create(
                ruta=data['ruta'],
                bus=data['bus'],
                fecha_salida=data['fecha_salida'],
                hora_salida=data['hora_salida'],
                defaults={
                    'precio_base': data['precio_base'],
                    'precio_cama': data['precio_cama'],
                }
            )
            if not created and servicio.precio_cama == 0:
                servicio.precio_cama = data['precio_cama']
                servicio.save(update_fields=['precio_cama'])

            self.crear_asientos(servicio)
        
        self.stdout.write('  OK Servicios y asientos creados')
    
    def crear_asientos(self, servicio):
        """Crea asientos numerados para un servicio."""
        capacidad = servicio.bus.capacidad
        for numero in range(1, capacidad + 1):
            tipo = (
                Asiento.Tipo.CAMA
                if numero <= servicio.bus.cantidad_cama
                else Asiento.Tipo.SEMICAMA
            )
            asiento, creado = Asiento.objects.get_or_create(
                servicio=servicio,
                numero=numero,
                defaults={'tipo': tipo},
            )
            if not creado and not asiento.ocupado and asiento.tipo != tipo:
                asiento.tipo = tipo
                asiento.save(update_fields=['tipo'])