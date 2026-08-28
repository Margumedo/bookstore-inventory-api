"""
Tests de los endpoints CRUD, filtros y paginacion.
"""

import pytest
from rest_framework.test import APIClient

from books.tests.factories import BookFactory


BOOKS_URL = '/api/v1/books/'


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


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
class TestBookCRUD:
    def test_create_book(self, api_client):
        response = api_client.post(BOOKS_URL, _payload(), format='json')
        assert response.status_code == 201
        assert response.data['isbn'] == '9788437604947'
        assert response.data['selling_price_local'] is None
        assert response.data['id'] is not None

    def test_create_book_invalid_isbn(self, api_client):
        response = api_client.post(BOOKS_URL, _payload(isbn='12345'), format='json')
        assert response.status_code == 400
        assert 'isbn' in response.data

    def test_create_book_duplicate_isbn(self, api_client):
        BookFactory(isbn='9788437604947')
        response = api_client.post(BOOKS_URL, _payload(), format='json')
        assert response.status_code == 400
        assert 'isbn' in response.data

    def test_list_books(self, api_client):
        BookFactory.create_batch(2)
        response = api_client.get(BOOKS_URL)
        assert response.status_code == 200
        assert response.data['count'] == 2
        assert len(response.data['results']) == 2

    def test_retrieve_book(self, api_client):
        book = BookFactory(title='El Quijote')
        response = api_client.get(f'{BOOKS_URL}{book.id}/')
        assert response.status_code == 200
        assert response.data['title'] == 'El Quijote'

    def test_retrieve_missing_book(self, api_client):
        response = api_client.get(f'{BOOKS_URL}99999/')
        assert response.status_code == 404

    def test_update_book(self, api_client):
        book = BookFactory(title='El Quijote', isbn='9788437604947')
        payload = _payload(title='El Quijote (edicion revisada)', stock_quantity=10)
        response = api_client.put(f'{BOOKS_URL}{book.id}/', payload, format='json')
        assert response.status_code == 200
        assert response.data['title'] == 'El Quijote (edicion revisada)'
        assert response.data['stock_quantity'] == 10

    def test_update_missing_book(self, api_client):
        response = api_client.put(f'{BOOKS_URL}99999/', _payload(), format='json')
        assert response.status_code == 404

    def test_partial_update_book(self, api_client):
        book = BookFactory(title='El Quijote', stock_quantity=25)
        response = api_client.patch(
            f'{BOOKS_URL}{book.id}/',
            {'stock_quantity': 8},
            format='json',
        )
        assert response.status_code == 200
        assert response.data['title'] == 'El Quijote'
        assert response.data['stock_quantity'] == 8

    def test_delete_book(self, api_client):
        book = BookFactory()
        response = api_client.delete(f'{BOOKS_URL}{book.id}/')
        assert response.status_code == 204
        follow_up = api_client.get(f'{BOOKS_URL}{book.id}/')
        assert follow_up.status_code == 404

    def test_delete_missing_book(self, api_client):
        response = api_client.delete(f'{BOOKS_URL}99999/')
        assert response.status_code == 404


@pytest.mark.django_db
class TestBookFilters:
    def test_list_filter_by_category(self, api_client):
        BookFactory(category='Fiction')
        BookFactory(category='Poetry')
        response = api_client.get(BOOKS_URL, {'category': 'Fiction'})
        assert response.status_code == 200
        assert response.data['count'] == 1
        assert response.data['results'][0]['category'] == 'Fiction'

    def test_search_by_category(self, api_client):
        BookFactory(category='Fiction')
        BookFactory(category='Poetry')
        response = api_client.get(f'{BOOKS_URL}search/', {'category': 'fiction'})
        assert response.status_code == 200
        assert response.data['count'] == 1
        assert response.data['results'][0]['category'] == 'Fiction'

    def test_search_requires_category(self, api_client):
        response = api_client.get(f'{BOOKS_URL}search/')
        assert response.status_code == 400
        assert 'category' in response.data

    def test_low_stock_default_threshold(self, api_client):
        low = BookFactory(stock_quantity=5)
        BookFactory(stock_quantity=15)
        response = api_client.get(f'{BOOKS_URL}low-stock/')
        assert response.status_code == 200
        ids = [item['id'] for item in response.data['results']]
        assert low.id in ids
        assert len(ids) == 1

    def test_low_stock_custom_threshold(self, api_client):
        included = BookFactory(stock_quantity=3)
        excluded = BookFactory(stock_quantity=8)
        response = api_client.get(f'{BOOKS_URL}low-stock/', {'threshold': 5})
        assert response.status_code == 200
        ids = [item['id'] for item in response.data['results']]
        assert included.id in ids
        assert excluded.id not in ids

    def test_low_stock_invalid_threshold(self, api_client):
        response = api_client.get(f'{BOOKS_URL}low-stock/', {'threshold': 'abc'})
        assert response.status_code == 400
        assert 'threshold' in response.data

    def test_list_is_paginated(self, api_client):
        BookFactory.create_batch(21)
        response = api_client.get(BOOKS_URL)
        assert response.status_code == 200
        assert response.data['count'] == 21
        assert len(response.data['results']) == 20
        assert response.data['next'] is not None
