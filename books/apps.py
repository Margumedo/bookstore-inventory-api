from django.apps import AppConfig
from django.conf import settings

import logging
import sys
from urllib.error import URLError
from urllib.request import Request, urlopen


class BooksConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = 'books'

    def ready(self):
        logger = logging.getLogger("startup")

        if not settings.STARTUP_EXCHANGE_HEALTHCHECK:
            logger.info("Startup exchange healthcheck disabled by environment.")
            return

        if not any(cmd in sys.argv for cmd in ("runserver", "gunicorn", "uvicorn", "daphne")):
            return

        request = Request(settings.EXCHANGE_RATE_API_URL, method="GET")
        try:
            with urlopen(request, timeout=settings.EXCHANGE_RATE_TIMEOUT_SECONDS) as response:
                logger.info(
                    "Exchange API startup healthcheck status=%s url=%s",
                    response.status,
                    settings.EXCHANGE_RATE_API_URL,
                )
        except URLError as exc:
            logger.warning(
                "Exchange API startup healthcheck failed url=%s reason=%s",
                settings.EXCHANGE_RATE_API_URL,
                exc,
            )
