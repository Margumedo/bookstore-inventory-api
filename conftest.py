"""
Configuracion global de pytest.

Debe ejecutarse antes de que Django inicialice settings.
"""

import os

os.environ.setdefault('DJANGO_SECRET_KEY', 'test-secret-key-not-for-production')
os.environ.setdefault('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver')
os.environ.setdefault(
    'DATABASE_URL',
    'postgres://bookstore_user:bookstore_pass@localhost:5432/bookstore',
)
