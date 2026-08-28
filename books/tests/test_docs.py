"""
Tests de health, OpenAPI y Swagger.
"""

import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
class TestDocsAndHealth:
    def test_health(self, api_client):
        response = api_client.get('/health/')
        assert response.status_code == 200
        assert response.json() == {'status': 'ok'}

    def test_openapi_schema_includes_search_category(self, api_client):
        response = api_client.get('/api/schema/')
        assert response.status_code == 200
        schema = response.content.decode()
        assert '/books/search/' in schema
        assert 'category' in schema

    def test_swagger_ui(self, api_client):
        response = api_client.get('/api/docs/')
        assert response.status_code == 200

    def test_root_redirects_to_docs(self, api_client):
        response = api_client.get('/', follow=False)
        assert response.status_code in (301, 302)
        assert '/api/docs/' in response.url
