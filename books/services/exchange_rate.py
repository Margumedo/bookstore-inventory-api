import json
import logging
from decimal import Decimal, InvalidOperation
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

CACHE_KEY_PREFIX = "exchange_rate_usd_to_"


class ExchangeRateUnavailable(Exception):
    """No live rate, no cache, and no default configured."""


def _cache_key(currency: str) -> str:
    return f"{CACHE_KEY_PREFIX}{currency.upper()}"


def _parse_rate_from_payload(payload: dict, currency: str) -> Decimal:
    rates = payload.get("rates")
    if not isinstance(rates, dict):
        raise ValueError("Invalid API response: missing 'rates' object.")
    raw = rates.get(currency.upper())
    if raw is None:
        raise ValueError(f"Currency '{currency}' not present in API rates.")
    return Decimal(str(raw))


def fetch_live_rate_usd_to(currency: str) -> Decimal:
    """Fetch USD -> currency rate from configured API. Raises on failure."""
    request = Request(settings.EXCHANGE_RATE_API_URL, method="GET")
    with urlopen(request, timeout=settings.EXCHANGE_RATE_TIMEOUT_SECONDS) as response:
        body = response.read().decode("utf-8")
    payload = json.loads(body)
    return _parse_rate_from_payload(payload, currency)


def get_exchange_rate_with_fallback(currency: str) -> tuple[Decimal, str]:
    """
    Hybrid: live API -> last cached successful rate -> DEFAULT_EXCHANGE_RATE env.
    Returns (rate, source) where source is 'live' | 'cache' | 'default'.
    Raises ExchangeRateUnavailable if nothing is available.
    """
    currency_key = currency.upper()

    try:
        rate = fetch_live_rate_usd_to(currency_key)
        cache.set(_cache_key(currency_key), str(rate), timeout=None)
        return rate, "live"
    except (URLError, HTTPError, TimeoutError, ValueError, json.JSONDecodeError, InvalidOperation) as exc:
        logger.warning(
            "Live exchange rate fetch failed currency=%s reason=%s",
            currency_key,
            exc,
        )

    cached = cache.get(_cache_key(currency_key))
    if cached is not None:
        try:
            return Decimal(str(cached)), "cache"
        except InvalidOperation:
            logger.warning("Invalid cached exchange rate for currency=%s", currency_key)

    default_raw = (settings.DEFAULT_EXCHANGE_RATE or "").strip()
    if default_raw:
        try:
            return Decimal(default_raw), "default"
        except InvalidOperation:
            logger.error("DEFAULT_EXCHANGE_RATE is not a valid decimal: %s", default_raw)

    raise ExchangeRateUnavailable(
        f"No exchange rate available for {currency_key} (API failed and no cache/default)."
    )
