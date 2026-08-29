"""
Tests de health, OpenAPI y Swagger.
"""

from unittest.mock import patch

import pytest
from django.db.utils import OperationalError
from rest_framework.test import APIClient

from books.exceptions import api_exception_handler


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
class TestDocsAndHealth:
    def test_health(self, api_client):
        response = api_client.get('/health/')
        assert response.status_code == 200
        assert response.json() == {'status': 'ok'}

    def test_health_returns_503_when_database_is_down(self, api_client):
        with patch('bookstore.views.connection.cursor') as mock_cursor:
            mock_cursor.side_effect = OperationalError('connection refused')
            response = api_client.get('/health/')
        assert response.status_code == 503
        assert response.json() == {
            'status': 'error',
            'detail': 'Base de datos no disponible.',
        }

    def test_openapi_schema_includes_search_category(self, api_client):
        response = api_client.get('/api/schema/')
        assert response.status_code == 200
        schema = response.content.decode()
        assert '/books/search/' in schema
        assert 'category' in schema
        assert 'gestion de inventario de librerias' in schema
        assert 'http://localhost:8000' not in schema

    def test_swagger_ui(self, api_client):
        response = api_client.get('/api/docs/')
        assert response.status_code == 200

    def test_root_redirects_to_docs(self, api_client):
        response = api_client.get('/', follow=False)
        assert response.status_code in (301, 302)
        assert '/api/docs/' in response.url


class TestUnhandledExceptions:
    def test_unexpected_error_returns_json_500(self):
        response = api_exception_handler(RuntimeError('boom'), {'request': None})
        assert response.status_code == 500
        assert response.data == {'detail': 'Error interno del servidor.'}
