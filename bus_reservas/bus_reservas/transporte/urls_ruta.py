"""
URLs de la aplicación TRANSPORTE - Rutas.

Endpoints para gestión de rutas.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RutaViewSet

router = DefaultRouter()
router.register(r'', RutaViewSet, basename='ruta')

urlpatterns = [
    path('', include(router.urls)),
]