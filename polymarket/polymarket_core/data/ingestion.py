from dataclasses import dataclass

from polymarket_core.adapters.market_adapter import MarketDataAdapter


@dataclass(frozen=True)
class MarketRecord:
    market_id: str
    question: str
    event_title: str
    category: str
    token_id: str
    reference_price: float
    expiration_iso: str
    cashout_iso: str
    probability: float
    liquidity: float
    volume_24h: float
    odds_edge: float
    one_hour_price_change: float
    one_week_price_change: float
    one_month_price_change: float
    one_year_price_change: float


class MarketIngestionService:
    def __init__(self, adapter: MarketDataAdapter) -> None:
        self.adapter = adapter

    def load(self) -> list[MarketRecord]:
        snapshots = self.adapter.fetch_markets()
        records: list[MarketRecord] = []
        for snapshot in snapshots:
            fair_price = 0.5
            edge = fair_price - snapshot.probability
            records.append(
                MarketRecord(
                    market_id=snapshot.market_id,
                    question=snapshot.question,
                    event_title=snapshot.event_title,
                    category=snapshot.category,
                    token_id=snapshot.yes_token_id,
                    reference_price=snapshot.yes_price,
                    expiration_iso=snapshot.expiration_iso,
                    cashout_iso=snapshot.cashout_iso,
                    probability=snapshot.probability,
                    liquidity=snapshot.liquidity,
                    volume_24h=snapshot.volume_24h,
                    odds_edge=edge,
                    one_hour_price_change=snapshot.one_hour_price_change,
                    one_week_price_change=snapshot.one_week_price_change,
                    one_month_price_change=snapshot.one_month_price_change,
                    one_year_price_change=snapshot.one_year_price_change,
                )
            )
        return records

