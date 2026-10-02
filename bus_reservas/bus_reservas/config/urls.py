"""
URLs principales del proyecto BUS RESERVAS API.

Define las rutas de la API, administración de Django y documentación Swagger.
"""

from django.urls import path, include
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from ventas.views import MisBoletosView, MisOrdenesView

urlpatterns = [
    # Interfaz web renderizada con templates Django.
    path('', include('config.web_urls')),
    
    # El acceso administrativo también usa el portal de templates propio.
    path(
        'admin/',
        RedirectView.as_view(pattern_name='gestion-inicio', permanent=False),
        name='admin-portal',
    ),
    
    # Documentación API (Swagger/OpenAPI)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # Endpoints de autenticación JWT estándar (SimpleJWT)
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Login personalizado con claims
    path('api/login/', include('usuarios.urls')),
    path('api/mis-boletos/', MisBoletosView.as_view(), name='api-mis-boletos'),
    path('api/mis-reservas/', MisOrdenesView.as_view(), name='api-mis-reservas'),
    
    # Endpoints de la API
    path('api/ciudades/', include('transporte.urls_ciudad')),
    path('api/terminales/', include('transporte.urls_terminal')),
    path('api/rutas/', include('transporte.urls_ruta')),
    path('api/buses/', include('transporte.urls_bus')),
    path('api/servicios/', include('transporte.urls_servicio')),
    path('api/asientos/', include('transporte.urls_asiento')),
    path('api/carrito/', include('carrito.urls')),
    path('api/carro-pasajes/', include('carrito.urls')),
    path('api/ventas/', include('ventas.urls')),
]