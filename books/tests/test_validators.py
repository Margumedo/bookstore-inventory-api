"""
Tests unitarios de normalizacion y checksum ISBN.
"""

import pytest
from django.core.exceptions import ValidationError

from books.validators import (
    build_isbn13,
    is_valid_isbn,
    normalize_isbn,
    validate_isbn,
)


# ISBN-13 del enunciado: El Quijote.
QUIJOTE_ISBN13 = '9788437604947'
QUIJOTE_ISBN13_HYPHENS = '978-84-376-0494-7'

# ISBN-10 valido conocido (The Art of Computer Programming, vol. 1, ejemplo clasico de checksum).
VALID_ISBN10 = '0306406152'
VALID_ISBN10_HYPHENS = '0-306-40615-2'
VALID_ISBN10_X = '043942089X'


class TestNormalizeIsbn:
    def test_strips_hyphens(self):
        assert normalize_isbn(QUIJOTE_ISBN13_HYPHENS) == QUIJOTE_ISBN13

    def test_strips_spaces(self):
        assert normalize_isbn('978 84 376 0494 7') == QUIJOTE_ISBN13

    def test_uppercases_isbn10_x(self):
        assert normalize_isbn('043942089x') == VALID_ISBN10_X

    def test_already_normalized_is_unchanged(self):
        assert normalize_isbn(QUIJOTE_ISBN13) == QUIJOTE_ISBN13


class TestIsbnChecksum:
    def test_valid_isbn13(self):
        assert is_valid_isbn(QUIJOTE_ISBN13) is True

    def test_valid_isbn10(self):
        assert is_valid_isbn(VALID_ISBN10) is True

    def test_valid_isbn10_with_x(self):
        assert is_valid_isbn(VALID_ISBN10_X) is True

    def test_invalid_isbn13_check_digit(self):
        assert is_valid_isbn('9788437604948') is False

    def test_invalid_length(self):
        assert is_valid_isbn('978843760494') is False

    def test_build_isbn13_roundtrip(self):
        assert is_valid_isbn(build_isbn13('978843760494')) is True
        assert build_isbn13('978843760494') == QUIJOTE_ISBN13


class TestValidateIsbn:
    def test_accepts_hyphenated_isbn13(self):
        assert validate_isbn(QUIJOTE_ISBN13_HYPHENS) == QUIJOTE_ISBN13

    def test_accepts_hyphenated_isbn10(self):
        assert validate_isbn(VALID_ISBN10_HYPHENS) == VALID_ISBN10

    def test_rejects_invalid_isbn(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_isbn('12345')
        assert exc_info.value.code == 'invalid_isbn'
