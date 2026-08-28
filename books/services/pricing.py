"""
Calculo de precio de venta sugerido.

No conoce HTTP: recibe costo, tasa y margen, y redondea a dos decimales.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

TWOPLACES = Decimal('0.01')


@dataclass(frozen=True)
class PriceCalculation:
    cost_usd: Decimal
    exchange_rate: Decimal
    cost_local: Decimal
    margin_percentage: int
    selling_price_local: Decimal
    currency: str


class PricingService:
    @staticmethod
    def calculate(
        cost_usd: Decimal,
        exchange_rate: Decimal,
        margin_percentage: int,
        currency: str,
    ) -> PriceCalculation:
        cost_usd = Decimal(str(cost_usd))
        exchange_rate = Decimal(str(exchange_rate))
        cost_local = (cost_usd * exchange_rate).quantize(TWOPLACES, rounding=ROUND_HALF_UP)
        multiplier = Decimal('1') + (Decimal(margin_percentage) / Decimal('100'))
        selling_price_local = (cost_local * multiplier).quantize(
            TWOPLACES,
            rounding=ROUND_HALF_UP,
        )
        return PriceCalculation(
            cost_usd=cost_usd.quantize(TWOPLACES, rounding=ROUND_HALF_UP),
            exchange_rate=exchange_rate,
            cost_local=cost_local,
            margin_percentage=margin_percentage,
            selling_price_local=selling_price_local,
            currency=currency,
        )
