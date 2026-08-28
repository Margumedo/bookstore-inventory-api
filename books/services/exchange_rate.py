"""
Servicio de tasas de cambio USD -> moneda local.

Consulta la API externa con timeout, cachea el resultado (tambien el
fallback) y comparte la cache entre workers via DatabaseCache.
"""

from __future__ import annotations

import logging
from decimal import Decimal, InvalidOperation

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

RATE_SOURCE_LIVE = 'live'
RATE_SOURCE_CACHE = 'cache'
RATE_SOURCE_FALLBACK = 'fallback'


class ExchangeRateUnavailableError(Exception):
    """No hay tasa live ni fallback usable."""


class ExchangeRateService:
    def get_rate(self, target_currency: str | None = None) -> tuple[Decimal, str]:
        currency = (target_currency or settings.LOCAL_CURRENCY).upper()
        cache_key = f'exchange_rate:USD:{currency}'

        cached_rate = self._cached_rate(cache_key)
        if cached_rate is not None:
            return cached_rate, RATE_SOURCE_CACHE

        try:
            rate = self._fetch_live_rate(currency)
        except (requests.RequestException, ValueError) as exc:
            logger.warning('Fallo la API de tasas (%s); se usa fallback.', exc)
            return self._fallback_rate(cache_key)

        self._store_rate(cache_key, rate)
        return rate, RATE_SOURCE_LIVE

    def _cached_rate(self, cache_key: str) -> Decimal | None:
        cached = cache.get(cache_key)
        if cached is None:
            return None
        if isinstance(cached, dict) and 'rate' in cached:
            return Decimal(str(cached['rate']))
        return Decimal(str(cached))

    def _store_rate(self, cache_key: str, rate: Decimal) -> None:
        cache.set(
            cache_key,
            {'rate': str(rate)},
            settings.EXCHANGE_RATE_CACHE_SECONDS,
        )

    def _fetch_live_rate(self, currency: str) -> Decimal:
        response = requests.get(
            settings.EXCHANGE_RATE_API_URL,
            timeout=settings.EXCHANGE_RATE_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return self._extract_rate(response.json(), currency)

    def _extract_rate(self, payload: object, currency: str) -> Decimal:
        if not isinstance(payload, dict):
            raise ValueError('La respuesta de tasas no es un objeto JSON.')

        rates = payload.get('rates')
        if not isinstance(rates, dict) or currency not in rates:
            raise ValueError(f'No hay tasa para {currency}.')

        try:
            rate = Decimal(str(rates[currency]))
        except (InvalidOperation, TypeError) as exc:
            raise ValueError(f'Tasa invalida para {currency}.') from exc

        if rate <= 0:
            raise ValueError(f'Tasa invalida para {currency}.')
        return rate

    def _fallback_rate(self, cache_key: str) -> tuple[Decimal, str]:
        rate = settings.DEFAULT_EXCHANGE_RATE
        if rate is None or rate <= 0:
            raise ExchangeRateUnavailableError('No se pudo obtener una tasa de cambio.')
        rate = Decimal(str(rate))
        self._store_rate(cache_key, rate)
        return rate, RATE_SOURCE_FALLBACK
