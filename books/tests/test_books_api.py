"""
Tests de los endpoints CRUD, filtros y paginacion.
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
import requests
from django.db import IntegrityError
from django.test import override_settings
from rest_framework.test import APIClient

from books.exceptions import validation_error_from_book_integrity

from books.tests.factories import BookFactory


BOOKS_URL = '/api/v1/books/'


def _ok_response(rates):
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {'base': 'USD', 'rates': rates}
    response.raise_for_status.return_value = None
    return response


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

    def test_check_constraint_is_not_reported_as_duplicate_isbn(self, api_client):
        error = IntegrityError(
            'new row for relation "books_book" violates check constraint '
            '"book_cost_usd_positive"'
        )
        with patch('books.models.Book.save', side_effect=error):
            response = api_client.post(BOOKS_URL, _payload(), format='json')
        assert response.status_code == 400
        assert 'isbn' not in response.data
        assert 'cost_usd' in response.data

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
        assert response.data['detail'] == 'No encontrado.'

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
        assert response.data['detail'] == 'No encontrado.'

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
        assert response.data['detail'] == 'No encontrado.'


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

    def test_low_stock_negative_threshold(self, api_client):
        response = api_client.get(f'{BOOKS_URL}low-stock/', {'threshold': -1})
        assert response.status_code == 400
        assert 'threshold' in response.data

    def test_list_is_paginated(self, api_client):
        BookFactory.create_batch(21)
        response = api_client.get(BOOKS_URL)
        assert response.status_code == 200
        assert response.data['count'] == 21
        assert len(response.data['results']) == 20
        assert response.data['next'] is not None


@pytest.mark.django_db
class TestCalculatePrice:
    @patch('books.services.exchange_rate.requests.get')
    def test_calculate_price_live(self, mock_get, api_client):
        mock_get.return_value = _ok_response({'EUR': '0.85'})
        book = BookFactory(cost_usd=Decimal('15.99'))

        response = api_client.post(f'{BOOKS_URL}{book.id}/calculate-price/')
        assert response.status_code == 200
        assert response.data['book_id'] == book.id
        assert response.data['cost_usd'] == '15.99'
        assert Decimal(response.data['exchange_rate']) == Decimal('0.85')
        assert response.data['cost_local'] == '13.59'
        assert response.data['margin_percentage'] == 40
        assert response.data['selling_price_local'] == '19.03'
        assert response.data['currency'] == 'EUR'
        assert response.data['rate_source'] == 'live'
        assert 'calculation_timestamp' in response.data

        book.refresh_from_db()
        assert book.selling_price_local == Decimal('19.03')

    @patch('books.services.exchange_rate.requests.get', side_effect=requests.Timeout)
    def test_calculate_price_fallback_on_timeout(self, mock_get, api_client):
        book = BookFactory(cost_usd=Decimal('15.99'))
        response = api_client.post(f'{BOOKS_URL}{book.id}/calculate-price/')
        assert response.status_code == 200
        assert response.data['rate_source'] == 'fallback'
        assert response.data['selling_price_local'] == '19.03'

    def test_calculate_price_missing_book(self, api_client):
        response = api_client.post(f'{BOOKS_URL}99999/calculate-price/')
        assert response.status_code == 404
        assert response.data['detail'] == 'No encontrado.'

    @override_settings(DEFAULT_EXCHANGE_RATE=Decimal('0'))
    @patch('books.services.exchange_rate.requests.get', side_effect=requests.Timeout)
    def test_calculate_price_unavailable_returns_503(self, mock_get, api_client):
        book = BookFactory(cost_usd=Decimal('15.99'))
        response = api_client.post(f'{BOOKS_URL}{book.id}/calculate-price/')
        assert response.status_code == 503


class TestIntegrityErrorMapping:
    def test_unique_isbn_maps_to_isbn_field(self):
        error = validation_error_from_book_integrity(
            IntegrityError(
                'duplicate key value violates unique constraint "books_book_isbn_key"'
            )
        )
        assert 'isbn' in error.detail

    def test_cost_check_maps_to_cost_usd(self):
        error = validation_error_from_book_integrity(
            IntegrityError(
                'new row violates check constraint "book_cost_usd_positive"'
            )
        )
        assert 'cost_usd' in error.detail
        assert 'isbn' not in error.detail

    def test_unknown_integrity_error_uses_detail(self):
        error = validation_error_from_book_integrity(IntegrityError('deadlock detected'))
        assert 'detail' in error.detail
        assert 'isbn' not in error.detail
