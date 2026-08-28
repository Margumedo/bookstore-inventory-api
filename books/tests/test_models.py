"""
Tests del modelo Book: persistencia, constraints y normalizacion.
"""

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from books.models import Book
from books.tests.factories import BookFactory
from books.validators import build_isbn13


QUIJOTE_ISBN = '9788437604947'


@pytest.mark.django_db
class TestBookModel:
    def test_create_persists_expected_fields(self):
        book = BookFactory(
            title='El Quijote',
            author='Miguel de Cervantes',
            isbn=QUIJOTE_ISBN,
            cost_usd=Decimal('15.99'),
            stock_quantity=25,
            category='Literatura Clasica',
            supplier_country='ES',
        )

        book.refresh_from_db()
        assert book.title == 'El Quijote'
        assert book.isbn == QUIJOTE_ISBN
        assert book.cost_usd == Decimal('15.99')
        assert book.selling_price_local is None
        assert book.stock_quantity == 25
        assert book.created_at is not None
        assert book.updated_at is not None

    def test_save_normalizes_isbn_and_country(self):
        book = BookFactory(
            isbn='978-84-376-0494-7',
            supplier_country='es',
        )

        book.refresh_from_db()
        assert book.isbn == QUIJOTE_ISBN
        assert book.supplier_country == 'ES'

    def test_str_includes_title_and_isbn(self):
        book = BookFactory(title='El Quijote', isbn=QUIJOTE_ISBN)
        assert str(book) == f'El Quijote ({QUIJOTE_ISBN})'

    def test_default_ordering_is_newest_first(self):
        first = BookFactory(title='Older')
        second = BookFactory(title='Newer')

        titles = list(Book.objects.values_list('title', flat=True))
        assert titles[0] == second.title
        assert titles[1] == first.title

    def test_isbn_uniqueness(self):
        BookFactory(isbn=QUIJOTE_ISBN)
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                BookFactory(isbn=QUIJOTE_ISBN)

    def test_rejects_invalid_isbn_on_save(self):
        with pytest.raises(ValidationError):
            BookFactory(isbn='1234567890')

    def test_cost_usd_must_be_positive(self):
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                Book.objects.create(
                    title='Invalid cost',
                    author='Author',
                    isbn=build_isbn13('978000000000'),
                    cost_usd=Decimal('0.00'),
                    stock_quantity=1,
                    category='Test',
                    supplier_country='ES',
                )

    def test_stock_zero_is_allowed(self):
        book = BookFactory(stock_quantity=0)
        book.refresh_from_db()
        assert book.stock_quantity == 0
