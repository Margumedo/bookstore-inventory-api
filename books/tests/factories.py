from decimal import Decimal

import factory

from books.models import Book


class BookFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Book

    title = factory.Sequence(lambda n: f'Sample Book {n}')
    author = factory.Sequence(lambda n: f'Author {n}')
    isbn = factory.Sequence(lambda n: f'{n:013d}')
    cost_usd = Decimal('15.99')
    selling_price_local = None
    stock_quantity = 25
    category = 'Literatura Clasica'
    supplier_country = 'ES'
