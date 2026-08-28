"""
Tests de validacion del BookSerializer.
"""

import pytest

from books.serializers import BookSerializer
from books.tests.factories import BookFactory
from books.validators import build_isbn13


def _payload(**overrides):
    data = {
        'title': 'El Quijote',
        'author': 'Miguel de Cervantes',
        'isbn': '978-84-376-0494-7',
        'cost_usd': '15.99',
        'stock_quantity': 25,
        'category': 'Literatura Clasica',
        'supplier_country': 'ES',
    }
    data.update(overrides)
    return data


@pytest.mark.django_db
class TestBookSerializer:
    def test_valid_payload_normalizes_isbn(self):
        serializer = BookSerializer(data=_payload())
        assert serializer.is_valid(), serializer.errors
        book = serializer.save()
        assert book.isbn == '9788437604947'
        assert book.selling_price_local is None

    def test_isbn_with_spaces_is_accepted(self):
        serializer = BookSerializer(data=_payload(isbn='978 84 376 0494 7'))
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['isbn'] == '9788437604947'

    def test_isbn10_is_accepted(self):
        serializer = BookSerializer(data=_payload(isbn='0-306-40615-2'))
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['isbn'] == '0306406152'

    def test_invalid_isbn_returns_error(self):
        serializer = BookSerializer(data=_payload(isbn='12345'))
        assert serializer.is_valid() is False
        assert 'isbn' in serializer.errors

    def test_duplicate_isbn_is_rejected(self):
        BookFactory(isbn='9788437604947')
        serializer = BookSerializer(data=_payload(isbn='978-84-376-0494-7'))
        assert serializer.is_valid() is False
        assert 'isbn' in serializer.errors

    def test_update_allows_same_isbn_on_same_instance(self):
        book = BookFactory(isbn='9788437604947')
        serializer = BookSerializer(
            instance=book,
            data=_payload(isbn='978-84-376-0494-7', title='El Quijote (edicion revisada)'),
        )
        assert serializer.is_valid(), serializer.errors
        updated = serializer.save()
        assert updated.pk == book.pk
        assert updated.title == 'El Quijote (edicion revisada)'

    def test_cost_usd_must_be_greater_than_zero(self):
        serializer = BookSerializer(data=_payload(cost_usd='0'))
        assert serializer.is_valid() is False
        assert 'cost_usd' in serializer.errors

    def test_negative_cost_usd_is_rejected(self):
        serializer = BookSerializer(data=_payload(cost_usd='-1.00'))
        assert serializer.is_valid() is False
        assert 'cost_usd' in serializer.errors

    def test_negative_stock_is_rejected(self):
        serializer = BookSerializer(data=_payload(stock_quantity=-1))
        assert serializer.is_valid() is False
        assert 'stock_quantity' in serializer.errors

    def test_zero_stock_is_allowed(self):
        serializer = BookSerializer(data=_payload(stock_quantity=0))
        assert serializer.is_valid(), serializer.errors

    def test_supplier_country_is_uppercased(self):
        serializer = BookSerializer(data=_payload(supplier_country='es'))
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['supplier_country'] == 'ES'

    def test_invalid_supplier_country(self):
        serializer = BookSerializer(data=_payload(supplier_country='ESP'))
        assert serializer.is_valid() is False
        assert 'supplier_country' in serializer.errors

    def test_selling_price_local_is_read_only(self):
        serializer = BookSerializer(
            data=_payload(selling_price_local='19.03'),
        )
        assert serializer.is_valid(), serializer.errors
        book = serializer.save()
        assert book.selling_price_local is None

    def test_unique_isbn_uses_normalized_value(self):
        BookFactory(isbn=build_isbn13('978000000001'))
        serializer = BookSerializer(data=_payload(isbn=build_isbn13('978000000001')))
        assert serializer.is_valid() is False
        assert 'isbn' in serializer.errors

    def test_required_fields(self):
        serializer = BookSerializer(data={})
        assert serializer.is_valid() is False
        for field in ('title', 'author', 'isbn', 'cost_usd', 'category', 'supplier_country'):
            assert field in serializer.errors
