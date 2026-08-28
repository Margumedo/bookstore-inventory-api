"""
Configuracion global de pytest.

Debe ejecutarse antes de que Django inicialice settings.
"""

import os

import pytest

os.environ.setdefault('DJANGO_SECRET_KEY', 'test-secret-key-not-for-production')
os.environ.setdefault('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver')
os.environ.setdefault(
    'DATABASE_URL',
    'postgres://bookstore_user:bookstore_pass@localhost:5432/bookstore',
)


@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        from django.core.management import call_command

        call_command('createcachetable', verbosity=0)


@pytest.fixture(autouse=True)
def _clear_cache(db):
    from django.core.cache import cache

    cache.clear()
