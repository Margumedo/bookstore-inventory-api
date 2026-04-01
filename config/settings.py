import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_DIR = BASE_DIR / "environments"

DJANGO_ENV = os.getenv("DJANGO_ENV", "dev").lower()
DOTENV_FILE_MAP = {
    "dev": ENV_DIR / ".env.dev",
    "qa": ENV_DIR / ".env.qa",
    "prod": ENV_DIR / ".env.prod",
}
load_dotenv(DOTENV_FILE_MAP.get(DJANGO_ENV, ENV_DIR / ".env.dev"))


class EnvironmentFilter(logging.Filter):
    def filter(self, record):
        record.environment = DJANGO_ENV
        return True


SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-env")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "books.apps.BooksConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

if "test" in sys.argv:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DB_NAME", "bookstore_inventory"),
            "USER": os.getenv("DB_USER", "bookstore"),
            "PASSWORD": os.getenv("DB_PASSWORD", "bookstore"),
            "HOST": os.getenv("DB_HOST", "localhost"),
            "PORT": os.getenv("DB_PORT", "5432"),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es-co"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOCAL_CURRENCY = os.getenv("LOCAL_CURRENCY", "VES")
DEFAULT_EXCHANGE_RATE = os.getenv("DEFAULT_EXCHANGE_RATE", "")
EXCHANGE_RATE_TIMEOUT_SECONDS = int(os.getenv("EXCHANGE_RATE_TIMEOUT_SECONDS", "5"))
STARTUP_EXCHANGE_HEALTHCHECK = (
    os.getenv("STARTUP_EXCHANGE_HEALTHCHECK", "true").lower() == "true"
)
EXCHANGE_RATE_API_URL = os.getenv(
    "EXCHANGE_RATE_API_URL", "https://api.exchangerate-api.com/v4/latest/USD"
)

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "bookstore-inventory-cache",
    }
}

PRICING_MARGIN_PERCENTAGE = int(os.getenv("PRICING_MARGIN_PERCENTAGE", "40"))

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": int(os.getenv("PAGE_SIZE", "20")),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Bookstore Inventory API",
    "DESCRIPTION": "API REST para gestion de inventario de librerias. Hecho con cariño by Maicol Argumedo",
    "VERSION": "1.0.0",
}

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "environment": {
            "()": EnvironmentFilter,
        }
    },
    "formatters": {
        "standard": {
            "format": (
                "%(asctime)s level=%(levelname)s logger=%(name)s env=%(environment)s "
                "message=%(message)s"
            ),
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "filters": ["environment"],
            "formatter": "standard",
        }
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
}

logging.getLogger("startup").info(
    "Startup config loaded debug=%s local_currency=%s db_host=%s",
    DEBUG,
    LOCAL_CURRENCY,
    DATABASES["default"].get("HOST", "n/a"),
)
