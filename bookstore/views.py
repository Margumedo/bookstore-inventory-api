"""
Vistas de infraestructura (health, etc.).
"""

from django.db import DatabaseError, connection
from django.http import JsonResponse


def health(_request):
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
    except DatabaseError:
        return JsonResponse(
            {'status': 'error', 'detail': 'Base de datos no disponible.'},
            status=503,
        )
    return JsonResponse({'status': 'ok'})
