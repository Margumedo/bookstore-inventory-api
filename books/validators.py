"""
Validacion y normalizacion de ISBN.

El enunciado pide ISBN-10 o ISBN-13 y no admite duplicados. El ejemplo incluye
guiones, asi que la API acepta separadores comunes y persiste solo el valor
normalizado.
"""

from __future__ import annotations

import re

from django.core.exceptions import ValidationError


ISBN_SEPARATORS_RE = re.compile(r'[\s-]+')


def normalize_isbn(value: str) -> str:
    """Elimina espacios y guiones, y unifica la X de ISBN-10 a mayuscula."""
    if value is None:
        return ''
    return ISBN_SEPARATORS_RE.sub('', str(value)).upper()


def isbn13_check_digit(body12: str) -> str:
    """Calcula el digito de control de un cuerpo ISBN-13 de 12 digitos."""
    if len(body12) != 12 or not body12.isdigit():
        raise ValueError('ISBN-13 body must be exactly 12 digits.')
    total = sum(int(digit) * (1 if index % 2 == 0 else 3) for index, digit in enumerate(body12))
    return str((10 - (total % 10)) % 10)


def build_isbn13(body12: str) -> str:
    """Construye un ISBN-13 valido a partir de 12 digitos."""
    return f'{body12}{isbn13_check_digit(body12)}'


def _is_valid_isbn10(value: str) -> bool:
    if len(value) != 10:
        return False
    total = 0
    for index, char in enumerate(value):
        if index == 9 and char == 'X':
            digit = 10
        elif char.isdigit():
            digit = int(char)
        else:
            return False
        total += digit * (10 - index)
    return total % 11 == 0


def _is_valid_isbn13(value: str) -> bool:
    if len(value) != 13 or not value.isdigit():
        return False
    total = sum(int(digit) * (1 if index % 2 == 0 else 3) for index, digit in enumerate(value))
    return total % 10 == 0


def is_valid_isbn(value: str) -> bool:
    """True si el valor (ya normalizado) es un ISBN-10 o ISBN-13 con checksum."""
    if len(value) == 10:
        return _is_valid_isbn10(value)
    if len(value) == 13:
        return _is_valid_isbn13(value)
    return False


def validate_isbn(value: str) -> str:
    """
    Normaliza y valida un ISBN.

    Retorna el valor normalizado o lanza ValidationError.
    """
    normalized = normalize_isbn(value)
    if not is_valid_isbn(normalized):
        raise ValidationError(
            'ISBN must be a valid ISBN-10 or ISBN-13 (digits, optional hyphens or spaces).',
            code='invalid_isbn',
        )
    return normalized
