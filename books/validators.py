"""
Validacion y normalizacion de ISBN.

El enunciado pide 10 o 13 digitos y no admite duplicados. El ejemplo incluye
guiones, asi que la API acepta separadores comunes y persiste solo el valor
normalizado.
"""

from __future__ import annotations

import re

from django.core.exceptions import ValidationError


ISBN_SEPARATORS_RE = re.compile(r'[\s-]+')

ISBN_INVALID_MESSAGE = 'El ISBN debe contener 10 o 13 digitos.'
ISBN_DUPLICATE_MESSAGE = 'Ya existe un libro con este ISBN.'


def normalize_isbn(value: str) -> str:
    """Elimina espacios y guiones."""
    if value is None:
        return ''
    return ISBN_SEPARATORS_RE.sub('', str(value))


def is_valid_isbn(value: str) -> bool:
    """True si el valor (ya normalizado) tiene exactamente 10 o 13 digitos."""
    return len(value) in (10, 13) and value.isdigit()


def validate_isbn(value: str) -> str:
    """
    Normaliza y valida un ISBN.

    Retorna el valor normalizado o lanza ValidationError.
    """
    normalized = normalize_isbn(value)
    if not is_valid_isbn(normalized):
        raise ValidationError(
            ISBN_INVALID_MESSAGE,
            code='invalid_isbn',
        )
    return normalized
