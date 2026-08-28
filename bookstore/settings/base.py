"""
Configuracion base del proyecto Django.
Compartida entre development y production.
"""

from decimal import Decimal
from pathlib import Path

from decouple import config, Csv
import dj_database_url


# Rutas base del proyecto.
# BASE_DIR apunta a la raiz del repositorio (un nivel arriba de bookstore/).
BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config('DJANGO_SECRET_KEY')

ALLOWED_HOSTS = config(
    'DJANGO_ALLOWED_HOSTS',
    default='localhost,127.0.0.1',
    cast=Csv(),
)


# Aplicaciones instaladas

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Terceros
    'rest_framework',
    'drf_spectacular',
    # Locales
    'books',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'bookstore.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'bookstore.wsgi.application'


# Base de datos
# PostgreSQL en todos los entornos para mantener paridad dev/prod.

DATABASES = {
    'default': dj_database_url.config(
        default='postgres://bookstore_user:bookstore_pass@localhost:5432/bookstore',
        conn_max_age=600,
    )
}


# Validacion de passwords

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internacionalizacion

LANGUAGE_CODE = 'es'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Archivos estaticos

STATIC_URL = 'static/'

STATIC_ROOT = BASE_DIR / 'staticfiles'


# Clave primaria por defecto

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Django REST Framework

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}


# drf-spectacular (Swagger / OpenAPI)

SPECTACULAR_SETTINGS = {
    'TITLE': 'Bookstore Inventory API',
    'DESCRIPTION': 'API REST para gestion de inventario de librerias con validacion de precios en tiempo real.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}


# Configuracion de negocio

LOCAL_CURRENCY = config('LOCAL_CURRENCY', default='EUR')

DEFAULT_EXCHANGE_RATE = config('DEFAULT_EXCHANGE_RATE', default='0.85', cast=Decimal)

PROFIT_MARGIN_PERCENTAGE = config('PROFIT_MARGIN_PERCENTAGE', default='40', cast=int)

EXCHANGE_RATE_API_URL = config(
    'EXCHANGE_RATE_API_URL',
    default='https://api.exchangerate-api.com/v4/latest/USD',
)

EXCHANGE_RATE_TIMEOUT_SECONDS = config(
    'EXCHANGE_RATE_TIMEOUT_SECONDS',
    default='5',
    cast=int,
)

EXCHANGE_RATE_CACHE_SECONDS = config(
    'EXCHANGE_RATE_CACHE_SECONDS',
    default='600',
    cast=int,
)


CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'bookstore-exchange-rates',
        'TIMEOUT': EXCHANGE_RATE_CACHE_SECONDS,
    }
}
