"""
Tests unitarios de normalizacion y formato ISBN.
"""

import pytest
from django.core.exceptions import ValidationError

from books.validators import is_valid_isbn, normalize_isbn, validate_isbn


QUIJOTE_ISBN13 = '9788437604947'
QUIJOTE_ISBN13_HYPHENS = '978-84-376-0494-7'
ISBN10_DIGITS = '0306406152'
ISBN10_HYPHENS = '0-306-40615-2'
TEN_DIGIT_ISBN = '1111111111'
THIRTEEN_DIGIT_ISBN = '1111111111111'


class TestNormalizeIsbn:
    def test_strips_hyphens(self):
        assert normalize_isbn(QUIJOTE_ISBN13_HYPHENS) == QUIJOTE_ISBN13

    def test_strips_spaces(self):
        assert normalize_isbn('978 84 376 0494 7') == QUIJOTE_ISBN13

    def test_already_normalized_is_unchanged(self):
        assert normalize_isbn(QUIJOTE_ISBN13) == QUIJOTE_ISBN13


class TestIsbnFormat:
    def test_accepts_10_digits_without_checksum(self):
        assert is_valid_isbn(TEN_DIGIT_ISBN) is True
        assert validate_isbn(TEN_DIGIT_ISBN) == TEN_DIGIT_ISBN

    def test_accepts_13_digits_without_checksum(self):
        assert is_valid_isbn(THIRTEEN_DIGIT_ISBN) is True
        assert validate_isbn(THIRTEEN_DIGIT_ISBN) == THIRTEEN_DIGIT_ISBN

    def test_accepts_10_and_13_digit_values_regardless_of_checksum(self):
        assert validate_isbn('1234567890') == '1234567890'
        assert validate_isbn('1234567890123') == '1234567890123'

    def test_rejects_wrong_length(self):
        assert is_valid_isbn('978843760494') is False
        assert is_valid_isbn('12345') is False

    def test_rejects_isbn10_check_digit_x(self):
        assert is_valid_isbn('043942089X') is False


class TestValidateIsbn:
    def test_accepts_hyphenated_isbn13(self):
        assert validate_isbn(QUIJOTE_ISBN13_HYPHENS) == QUIJOTE_ISBN13

    def test_accepts_hyphenated_isbn10(self):
        assert validate_isbn(ISBN10_HYPHENS) == ISBN10_DIGITS

    def test_rejects_invalid_isbn(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_isbn('12345')
        assert exc_info.value.code == 'invalid_isbn'
