from decimal import Decimal

import factory

from books.models import Book
from books.validators import build_isbn13


class BookFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Book

    title = factory.Sequence(lambda n: f'Sample Book {n}')
    author = factory.Sequence(lambda n: f'Author {n}')
    isbn = factory.Sequence(lambda n: build_isbn13(f'978{n:09d}'))
    cost_usd = Decimal('15.99')
    selling_price_local = None
    stock_quantity = 25
    category = 'Literatura Clasica'
    supplier_country = 'ES'
