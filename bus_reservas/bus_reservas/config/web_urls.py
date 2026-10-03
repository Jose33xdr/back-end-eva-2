"""Rutas del sitio web renderizado: b?squeda, autenticaci?n y gesti?n administrativa."""
from django.urls import path

from . import web_views


urlpatterns = [
    path('', web_views.home, name='home'),
    path('viajes/', web_views.buscar_viajes, name='buscar-viajes'),
    path('viajes/<int:servicio_id>/', web_views.detalle_servicio, name='detalle-servicio'),
    path('login/', web_views.iniciar_sesion, name='login-web'),
    path('registro/', web_views.registro, name='registro-web'),
    path('logout/', web_views.cerrar_sesion, name='logout-web'),
    path('carro/', web_views.carro, name='carro-web'),
    path('carro/quitar/<int:item_id>/', web_views.quitar_item_carro, name='carro-quitar-web'),
    path('carro/confirmar/', web_views.confirmar_compra, name='carro-confirmar-web'),
    path('mis-reservas/', web_views.mis_reservas, name='mis-reservas-web'),
    path(
        'documentacion/swagger/',
        web_views.documentacion_web,
        {'documento': 'swagger'},
        name='swagger-web',
    ),
    path(
        'documentacion/redoc/',
        web_views.documentacion_web,
        {'documento': 'redoc'},
        name='redoc-web',
    ),
    path(
        'documentacion/openapi/',
        web_views.documentacion_web,
        {'documento': 'openapi'},
        name='openapi-web',
    ),
    path(
        'mis-reservas/<int:orden_id>/pasajes/<int:item_id>/asientos/',
        web_views.ver_asientos_reserva,
        name='reserva-ver-asientos',
    ),
    path(
        'mis-reservas/<int:orden_id>/cancelar/',
        web_views.cancelar_mis_pasajes,
        name='mis-pasajes-cancelar-web',
    ),
    path('compras/<int:orden_id>/', web_views.detalle_orden, name='orden-detalle-web'),
    path('gestion/', web_views.gestion_inicio, name='gestion-inicio'),
    path('gestion/ordenes/', web_views.gestion_ordenes, name='gestion-ordenes'),
    path(
        'gestion/ordenes/<int:orden_id>/estado/',
        web_views.gestion_cambiar_estado,
        name='gestion-orden-cambiar-estado',
    ),
    path('gestion/<str:recurso>/', web_views.gestion_lista, name='gestion-lista'),
    path(
        'gestion/<str:recurso>/nuevo/',
        web_views.gestion_formulario,
        name='gestion-nuevo',
    ),
    path(
        'gestion/<str:recurso>/<int:objeto_id>/editar/',
        web_views.gestion_formulario,
        name='gestion-editar',
    ),
    path(
        'gestion/<str:recurso>/<int:objeto_id>/eliminar/',
        web_views.gestion_eliminar,
        name='gestion-eliminar',
    ),
]
