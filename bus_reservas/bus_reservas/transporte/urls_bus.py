"""
URLs de la aplicación TRANSPORTE - Buses.

Endpoints para gestión de buses.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BusViewSet

router = DefaultRouter()
router.register(r'', BusViewSet, basename='bus')

urlpatterns = [
    path('', include(router.urls)),
]