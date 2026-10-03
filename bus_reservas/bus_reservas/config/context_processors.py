"""Context processors del portal web para exponer metadatos institucionales."""
import os
from datetime import date


def datos_alumno(request):
    """Expone en todas las páginas el nombre, sección y año para el footer académico."""
    return {
        'alumno_nombre': os.environ.get('ALUMNO_NOMBRE', 'Completar nombre completo'),
        'alumno_seccion': os.environ.get('ALUMNO_SECCION', 'Completar sección'),
        'anio_actual': date.today().year,
    }
