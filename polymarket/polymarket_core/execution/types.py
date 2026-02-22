from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutedOrder:
    market_id: str
    token_id: str
    side: str
    notional_usd: float
    expected_edge: float
    status: str
    venue_order_id: str | None = None
    message: str | None = None

