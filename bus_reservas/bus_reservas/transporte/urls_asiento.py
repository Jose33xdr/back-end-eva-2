"""
URLs de la aplicación TRANSPORTE - Asientos.

Endpoints para consultar asientos (solo lectura).
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AsientoViewSet

router = DefaultRouter()
router.register(r'', AsientoViewSet, basename='asiento')

urlpatterns = [
    path('', include(router.urls)),
]