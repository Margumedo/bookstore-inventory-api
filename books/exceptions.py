"""
Errores HTTP en espanol.
"""

import logging

from django.db import IntegrityError
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import MethodNotAllowed, NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

from books.validators import ISBN_DUPLICATE_MESSAGE

logger = logging.getLogger(__name__)


def validation_error_from_book_integrity(exc: IntegrityError) -> ValidationError:
    """Traduce un IntegrityError de Book a un 400 por campo, no siempre ISBN."""
    text = str(exc).lower()
    cause = exc.__cause__
    if cause is not None:
        text = f'{text} {cause}'.lower()
        constraint = getattr(getattr(cause, 'diag', None), 'constraint_name', None) or ''
        text = f'{text} {constraint}'.lower()

    if 'isbn' in text:
        return ValidationError({'isbn': [ISBN_DUPLICATE_MESSAGE]})
    if 'cost_usd' in text or 'book_cost_usd_positive' in text:
        return ValidationError({'cost_usd': ['cost_usd debe ser mayor que 0.']})
    if 'stock' in text or 'book_stock_non_negative' in text:
        return ValidationError(
            {'stock_quantity': ['stock_quantity debe ser mayor o igual a 0.']}
        )
    return ValidationError({'detail': ['No se pudo guardar el libro.']})


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        logger.exception('Error no controlado.')
        return Response(
            {'detail': 'Error interno del servidor.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    if isinstance(exc, (NotFound, Http404)) or response.status_code == 404:
        response.data = {'detail': 'No encontrado.'}
    elif isinstance(exc, MethodNotAllowed):
        response.data = {'detail': 'Metodo no permitido.'}

    return response
