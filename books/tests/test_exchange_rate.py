"""
Tests del servicio de tasas de cambio. La API externa siempre se mockea.
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
import requests
from django.core.cache import cache
from django.test import override_settings

from books.services.exchange_rate import (
    RATE_SOURCE_CACHE,
    RATE_SOURCE_FALLBACK,
    RATE_SOURCE_LIVE,
    ExchangeRateService,
    ExchangeRateUnavailableError,
)


def _ok_response(rates):
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {'base': 'USD', 'rates': rates}
    response.raise_for_status.return_value = None
    return response


@pytest.mark.django_db
class TestExchangeRateService:
    @patch('books.services.exchange_rate.requests.get')
    def test_live_rate(self, mock_get):
        mock_get.return_value = _ok_response({'EUR': '0.85'})
        rate, source = ExchangeRateService().get_rate('EUR')
        assert rate == Decimal('0.85')
        assert source == RATE_SOURCE_LIVE
        mock_get.assert_called_once()

    @patch('books.services.exchange_rate.requests.get')
    def test_cache_hit_skips_http(self, mock_get):
        mock_get.return_value = _ok_response({'EUR': '0.85'})
        service = ExchangeRateService()
        service.get_rate('EUR')
        mock_get.reset_mock()

        rate, source = service.get_rate('EUR')
        assert rate == Decimal('0.85')
        assert source == RATE_SOURCE_CACHE
        mock_get.assert_not_called()

    @patch('books.services.exchange_rate.requests.get', side_effect=requests.Timeout)
    def test_timeout_uses_fallback(self, mock_get):
        rate, source = ExchangeRateService().get_rate('EUR')
        assert rate == Decimal('0.85')
        assert source == RATE_SOURCE_FALLBACK

    @patch('books.services.exchange_rate.requests.get')
    def test_invalid_payload_uses_fallback(self, mock_get):
        response = MagicMock()
        response.raise_for_status.return_value = None
        response.json.return_value = {'error': 'no rates'}
        mock_get.return_value = response
        rate, source = ExchangeRateService().get_rate('EUR')
        assert source == RATE_SOURCE_FALLBACK
        assert rate == Decimal('0.85')

    @patch('books.services.exchange_rate.requests.get')
    def test_missing_currency_uses_fallback(self, mock_get):
        mock_get.return_value = _ok_response({'MXN': '17.50'})
        rate, source = ExchangeRateService().get_rate('EUR')
        assert source == RATE_SOURCE_FALLBACK

    @override_settings(DEFAULT_EXCHANGE_RATE=Decimal('0'))
    @patch('books.services.exchange_rate.requests.get', side_effect=requests.ConnectionError)
    def test_unavailable_when_fallback_invalid(self, mock_get):
        cache.clear()
        with pytest.raises(ExchangeRateUnavailableError):
            ExchangeRateService().get_rate('EUR')
