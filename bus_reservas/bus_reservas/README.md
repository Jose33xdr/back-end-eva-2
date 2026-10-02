# BUS RESERVAS API

Sistema de reservas de pasajes de bus desarrollado con Django REST Framework para evaluación académica de Backend.

## 🚀 Tecnologías Utilizadas

- **Python 3.12+**
- **Django 5.1+**
- **Django REST Framework**
- **PostgreSQL** (base de datos requerida para la evaluación)
- **Simple JWT** (autenticación con tokens)
- **django-filter** (filtrado de consultas)
- **drf-spectacular** (documentación Swagger/OpenAPI)
- **psycopg2-binary** (driver PostgreSQL)
- **python-dotenv** (carga de variables desde `.env`)

## 📋 Requisitos Previos

- Python 3.12 o superior
- PostgreSQL 14+ instalado y corriendo
- pip (gestor de paquetes de Python)

## 🔧 Instalación y Configuración

### 1. Clonar/Crear el proyecto

```bash
cd bus_reservas
```

### 2. Crear entorno virtual e instalar dependencias

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate

# Instalar paquetes
pip install -r requirements.txt
```

### 3. Configurar base de datos

La evaluación exige PostgreSQL o MySQL (no SQLite). Crea la base de datos PostgreSQL:

```sql
CREATE DATABASE bus_reservas;
CREATE USER postgres WITH PASSWORD 'tu_password';
GRANT ALL PRIVILEGES ON DATABASE bus_reservas TO postgres;
```

### 4. Configurar variables de entorno

Copiar el archivo de ejemplo y editar:

```bash
cp .env.example .env
```

Editar `.env` con tus credenciales:

```env
DB_NAME=bus_reservas
DB_USER=postgres
DB_PASSWORD=tu_password_aqui
DB_HOST=localhost
DB_PORT=5432

SECRET_KEY=tu-clave-secreta-muy-segura
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
ALUMNO_NOMBRE=Tu nombre completo
ALUMNO_SECCION=Tu sección

JWT_ACCESS_TOKEN_LIFETIME=60
JWT_REFRESH_TOKEN_LIFETIME=1440
```

### 5. Ejecutar migraciones

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Cargar datos de prueba (opcional)

```bash
python manage.py cargar_datos_prueba
```

Esto crea:
- **Usuarios**: `admin` / `admin123` (ADMINISTRADOR), `pasajero` / `pasajero123` (PASAJERO)
- **Ciudades**: Santiago, Temuco, Concepción, Valparaíso, La Serena, Chillán, Valdivia y Puerto Montt
- **Terminales**: un terminal de prueba por ciudad
- **Rutas**: 11 recorridos de ejemplo, editables desde el panel de administración
- **Buses**: 3 buses con diferentes capacidades
- **Servicios**: Rutas con horarios y precios para los próximos días

### 7. Crear superusuario (opcional, si no usaste datos de prueba)

```bash
python manage.py createsuperuser
```

### 8. Ejecutar servidor

```bash
python manage.py runserver
```

El servidor estará disponible en: **http://localhost:8000**

La interfaz pública, pasajeros y administración está renderizada con templates de Django. Las URL web desconocidas muestran una página 404 con un botón para volver; las rutas API desconocidas conservan su respuesta 404. La barra superior ofrece accesos a Swagger Docs, ReDoc, OpenAPI y al panel administrador; las vistas de documentación incluyen navegación para volver. El panel de flota se encuentra en `/gestion/`; `/admin/` redirige a ese panel. El administrador puede crear, buscar, editar y eliminar ciudades, terminales, rutas, buses y viajes. Los datos se enlazan en los formularios: las ciudades creadas aparecen en terminales, los terminales en rutas, y las rutas y buses en los viajes. `config.settings_test` usa SQLite únicamente para pruebas automatizadas y vistas locales; la ejecución normal con `config.settings` requiere PostgreSQL, como exige la evaluación.

Para ejecutar las pruebas automatizadas sin un servidor PostgreSQL instalado:

```bash
python manage.py test config.tests --settings=config.settings_test
```

## 📚 Documentación API

- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/schema/
- **Swagger Docs con navegación**: http://localhost:8000/documentacion/swagger/
- **ReDoc con navegación**: http://localhost:8000/documentacion/redoc/
- **OpenAPI con navegación**: http://localhost:8000/documentacion/openapi/
- **Panel administrador con templates**: http://localhost:8000/gestion/
- **Alias del panel**: http://localhost:8000/admin/

## 🔐 Autenticación y Roles

El sistema usa **JWT (JSON Web Tokens)** con claims personalizados:

```json
{
  "user_id": 1,
  "username": "juan",
  "rol": "PASAJERO"
}
```

### Roles:

| Rol | Descripción | Permisos |
|-----|-------------|----------|
| **PASAJERO** | Usuario cliente | Ver servicios, gestionar carrito, checkout, ver sus reservas |
| **ADMINISTRADOR** | Usuario staff | CRUD completo (ciudades, terminales, rutas, buses, servicios), cambiar estados de órdenes |

### Endpoints de Autenticación:

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/login/` | Login personalizado (retorna access, refresh, usuario con rol) |
| POST | `/api/login/registro/` | Registrar nuevo pasajero |
| POST | `/api/auth/token/` | Obtener tokens (estándar SimpleJWT) |
| POST | `/api/auth/token/refresh/` | Renovar access token |
| POST | `/api/auth/token/verify/` | Verificar token |
| GET/PUT | `/api/login/perfil/` | Ver/actualizar perfil |
| POST | `/api/login/cambio-password/` | Cambiar contraseña |
| POST | `/api/login/logout/` | Cerrar sesión (blacklist refresh) |

## 🚌 Endpoints Principales

### Público (sin autenticación)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/servicios/` | Listar servicios con filtros |
| GET | `/api/servicios/buscar/` | Búsqueda pública de viajes |
| GET | `/api/servicios/{id}/` | Detalle de servicio con asientos |
| GET | `/api/servicios/{id}/asientos/` | Consultar asientos, tipo y tarifa |
| GET | `/api/rutas/` | Listar rutas |
| GET | `/api/ciudades/` | Listar ciudades |
| GET | `/api/terminales/` | Listar terminales |
| GET | `/api/buses/` | Listar buses |

### Pasajero (autenticado, rol PASAJERO)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/carrito/` | Ver carrito actual |
| POST | `/api/carrito/agregar/` | Agregar asiento al carrito |
| DELETE | `/api/carrito/quitar/{id}/` | Quitar asiento del carrito |
| DELETE | `/api/carrito/limpiar/` | Vaciar carrito |
| POST | `/api/ventas/checkout/` | Realizar checkout (crea orden PENDIENTE) |
| GET | `/api/mis-reservas/` | Listar mis órdenes |
| GET | `/api/mis-boletos/` | Listar boletos emitidos con código UUID |
| GET | `/api/ventas/{id}/` | Ver detalle de mi orden |

### Administrador (autenticado, rol ADMINISTRADOR)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/servicios/` | Crear servicio |
| PUT/PATCH | `/api/servicios/{id}/` | Editar servicio |
| DELETE | `/api/servicios/{id}/` | Eliminar servicio |
| CRUD | `/api/ciudades/`, `/api/terminales/`, `/api/rutas/`, `/api/buses/` | Gestión completa |
| GET | `/api/ventas/` | Ver todas las órdenes |
| PATCH | `/api/ventas/{id}/estado/` | Cambiar estado de orden |

La interfaz web de pasajeros y administradores utiliza templates Django con sesiones. El administrador puede gestionar ciudades, terminales, rutas, buses, servicios y estados de ventas desde `/gestion/`; Swagger y los endpoints JWT permanecen disponibles para integración.

## 🔍 Filtros Disponibles

### Servicios (`/api/servicios/`)

```bash
# Por ciudad origen
GET /api/servicios/?origen=Santiago

# Por ciudad destino
GET /api/servicios/?destino=Temuco

# Por fecha de salida
GET /api/servicios/?fecha=2026-10-15

# Por rango de precios
GET /api/servicios/?precio_min=10000&precio_max=30000

# Combinados
GET /api/servicios/?origen=Santiago&destino=Temuco&fecha=2026-10-15
```

## 💡 Flujo de Compra (Checkout)

1. **Pasajero** navega servicios públicos (`GET /api/servicios/`)
2. **Pasajero** agrega asientos al carrito (`POST /api/carrito/agregar/`)
   - El asiento NO se marca como ocupado aún
   - El carrito persiste después de logout
3. **Pasajero** confirma compra (`POST /api/ventas/checkout/`)
   - Sistema valida disponibilidad de asientos
   - Crea **Orden** con estado **PENDIENTE**
   - Crea **ItemsOrden** con precios **congelados**
   - Vacía el carrito
4. **Administrador** confirma pago (`PATCH /api/ventas/{id}/estado/` con `{"estado": "PAGADO"}`)
   - **Transacción atómica**: valida disponibilidad + marca asientos `ocupado=True`
   - Si no hay stock, rechaza la operación
5. **Administrador** puede cancelar (`PATCH /api/ventas/{id}/estado/` con `{"estado": "CANCELADO"}`)
   - Si era **PAGADO** → **CANCELADO**: libera asientos (`ocupado=False`)

## 🗃️ Estructura del Proyecto

```
bus_reservas/
├── config/                 # Configuración Django
│   ├── settings.py        # Settings principal
│   ├── urls.py            # URLs principales
│   └── wsgi.py
├── usuarios/              # App usuarios y auth
│   ├── models.py          # Usuario personalizado
│   ├── serializers.py     # Serializers auth/registro
│   ├── views.py           # Login, registro, perfil
│   ├── permissions.py     # Permisos por rol
│   ├── urls.py
│   └── management/commands/cargar_datos_prueba.py
├── transporte/            # App transporte
│   ├── models.py          # Ciudad, Terminal, Ruta, Bus, Servicio, Asiento
│   ├── serializers.py
│   ├── views.py           # ViewSets con filtros
│   ├── urls_*.py          # URLs por modelo
│   └── admin.py
├── carrito/               # App carrito persistente
│   ├── models.py          # Carro (OneToOne User), ItemCarro
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
├── ventas/                # App órdenes y checkout
│   ├── models.py          # Orden, ItemOrden (precio congelado)
│   ├── serializers.py
│   ├── views.py           # Checkout, cambio estado transaccional
│   └── urls.py
├── templates/
│   └── base.html          # Home con footer alumno
├── manage.py
├── requirements.txt
├── .env.example
└── README.md
```

## ✅ Validación Final

Ejecutar checklist:

```bash
# 1. Verificar configuración
python manage.py check

# 2. Crear migraciones
python manage.py makemigrations

# 3. Aplicar migraciones
python manage.py migrate

# 4. Cargar datos de prueba
python manage.py cargar_datos_prueba

# 5. Ejecutar servidor
python manage.py runserver
```

### Verificaciones:

- [ ] PostgreSQL configurado y conectando
- [ ] JWT funciona (login retorna access/refresh + rol)
- [ ] Claims de rol funcionan (PASAJERO/ADMINISTRADOR)
- [ ] Swagger funciona en `/api/docs/`
- [ ] Servicios públicos accesibles sin auth
- [ ] Carrito persiste después de logout
- [ ] Checkout crea orden PENDIENTE con precios congelados
- [ ] Stock (asientos) se descuenta solo al PAGADO
- [ ] Stock se libera al CANCELADO desde PAGADO
- [ ] Filtros funcionan en `/api/servicios/`
- [ ] Código comentado en todos los archivos
- [ ] Footer con datos alumno visible en `/`

## 👨‍🎓 Datos del Alumno

Editar `templates/base.html` para completar:

```html
<span class="footer-value">[TU NOMBRE COMPLETO]</span>
<span class="footer-value">[TU SECCIÓN]</span>
<span class="footer-value">2026</span>
```

## 📝 Notas Importantes

- **NO usa SQLite** - Configurado nativamente para PostgreSQL
- **Carro persistente** - OneToOne con Usuario, sobrevive al logout
- **Precios históricos** - ItemOrden guarda precio_unitario congelado
- **Control transaccional** - `transaction.atomic()` en checkout y cambio de estado
- **Sin over-engineering** - Arquitectura simple y defendible
- **Código comentado** - Todos los archivos tienen docstrings explicativos

## 🐛 Solución de Problemas

### Error de conexión PostgreSQL
Verificar que PostgreSQL esté corriendo y credenciales en `.env` sean correctas.

### Error "relation does not exist"
Ejecutar `python manage.py migrate` después de cambios en modelos.

### JWT "Token invalid"
Verificar `SECRET_KEY` en `.env` coincida con la usada para generar tokens.

### Permisos denegados
Verificar que el usuario pertenezca al grupo correcto (PASAJERO/ADMINISTRADOR) en Django Admin.

---

**Desarrollado para evaluación académica Backend - 2026**