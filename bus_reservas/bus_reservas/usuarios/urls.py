"""
URLs de la aplicación USUARIOS.

Endpoints de autenticación y gestión de usuarios.
"""

from django.urls import path
from .views import (
    CustomTokenObtainPairView,
    RegistroUsuarioView,
    PerfilUsuarioView,
    CambioPasswordView,
    logout_view
)

urlpatterns = [
    # Login personalizado con claims de rol
    path('', CustomTokenObtainPairView.as_view(), name='login'),
    
    # Registro de nuevos usuarios (rol PASAJERO por defecto)
    path('registro/', RegistroUsuarioView.as_view(), name='registro'),
    
    # Perfil del usuario autenticado
    path('perfil/', PerfilUsuarioView.as_view(), name='perfil'),
    
    # Cambio de contraseña
    path('cambio-password/', CambioPasswordView.as_view(), name='cambio-password'),
    
    # Logout (blacklist refresh token)
    path('logout/', logout_view, name='logout'),
]