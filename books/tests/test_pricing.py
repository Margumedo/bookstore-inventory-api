"""
Tests del calculo de precio sugerido.
"""

from decimal import Decimal

from books.services.pricing import PricingService


class TestPricingService:
    def test_example_from_spec(self):
        result = PricingService.calculate(
            cost_usd=Decimal('15.99'),
            exchange_rate=Decimal('0.85'),
            margin_percentage=40,
            currency='EUR',
        )
        assert result.cost_local == Decimal('13.59')
        assert result.selling_price_local == Decimal('19.03')
        assert result.margin_percentage == 40
        assert result.currency == 'EUR'

    def test_rounds_half_up(self):
        result = PricingService.calculate(
            cost_usd=Decimal('10.00'),
            exchange_rate=Decimal('0.333'),
            margin_percentage=40,
            currency='EUR',
        )
        assert result.cost_local == Decimal('3.33')
        assert result.selling_price_local == Decimal('4.66')
