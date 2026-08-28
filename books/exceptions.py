"""
Errores HTTP en espanol.
"""

from django.http import Http404
from rest_framework.exceptions import MethodNotAllowed, NotFound
from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None

    if isinstance(exc, (NotFound, Http404)) or response.status_code == 404:
        response.data = {'detail': 'No encontrado.'}
    elif isinstance(exc, MethodNotAllowed):
        response.data = {'detail': 'Metodo no permitido.'}

    return response
