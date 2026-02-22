from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class MarketSnapshot:
    market_id: str
    question: str
    event_title: str
    category: str
    probability: float
    liquidity: float
    volume_24h: float
    yes_token_id: str
    yes_price: float
    expiration_iso: str
    cashout_iso: str
    one_hour_price_change: float
    one_week_price_change: float
    one_month_price_change: float
    one_year_price_change: float


class MarketDataAdapter(Protocol):
    def fetch_markets(self) -> list[MarketSnapshot]:
        """Return the latest market snapshots from any provider."""

