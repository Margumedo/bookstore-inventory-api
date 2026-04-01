from decimal import ROUND_HALF_UP, Decimal

TWO_PLACES = Decimal("0.01")
MARGIN_MULTIPLIER = Decimal("1.40")


def compute_local_cost_and_selling(
    cost_usd: Decimal,
    exchange_rate: Decimal,
) -> tuple[Decimal, Decimal]:
    """
    cost_local = cost_usd * rate (2 decimals, HALF_UP).
    selling_price_local = cost_local * 1.40 (40% margin on local cost).
    """
    cost_local = (cost_usd * exchange_rate).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
    selling = (cost_local * MARGIN_MULTIPLIER).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
    return cost_local, selling
