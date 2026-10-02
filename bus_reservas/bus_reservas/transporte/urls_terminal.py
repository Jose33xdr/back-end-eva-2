"""
URLs de la aplicación TRANSPORTE - Terminales.

Endpoints para gestión de terminales.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TerminalViewSet

router = DefaultRouter()
router.register(r'', TerminalViewSet, basename='terminal')

urlpatterns = [
    path('', include(router.urls)),
]