"""
URLs de la aplicación TRANSPORTE - Ciudades.

Endpoints para gestión de ciudades.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CiudadViewSet

router = DefaultRouter()
router.register(r'', CiudadViewSet, basename='ciudad')

urlpatterns = [
    path('', include(router.urls)),
]