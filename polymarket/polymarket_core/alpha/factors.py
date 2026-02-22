from dataclasses import dataclass

from polymarket_core.data.ingestion import MarketRecord


@dataclass(frozen=True)
class ScoredMarket:
    market_id: str
    token_id: str
    reference_price: float
    score: float
    probability: float
    liquidity: float
    edge_component: float
    momentum_component: float
    volume_component: float
    liquidity_penalty_component: float


class FactorEngine:
    """
    Lightweight factor model for event markets.
    The score rewards positive pricing edge and penalizes weak liquidity.
    """

    PRESET_WEIGHTS: dict[str, dict[str, float]] = {
        "balanced": {"edge": 1.00, "momentum": 0.15, "volume": 0.05, "liquidity_penalty": -0.10},
        "contrarian": {"edge": 1.10, "momentum": -0.20, "volume": 0.05, "liquidity_penalty": -0.12},
        "momentum": {"edge": 0.65, "momentum": 0.55, "volume": 0.05, "liquidity_penalty": -0.08},
        "liquidity": {"edge": 0.85, "momentum": 0.10, "volume": 0.25, "liquidity_penalty": -0.06},
    }

    def __init__(
        self,
        strategy_name: str = "balanced",
        custom_weights: dict[str, float] | None = None,
    ) -> None:
        self.strategy_name = strategy_name.strip().lower() if strategy_name else "balanced"
        base = self.PRESET_WEIGHTS.get(self.strategy_name, self.PRESET_WEIGHTS["balanced"]).copy()
        if custom_weights:
            for key in ("edge", "momentum", "volume", "liquidity_penalty"):
                if key in custom_weights:
                    base[key] = float(custom_weights[key])
            self.strategy_name = "custom"
        self.weights = base

    def score(self, records: list[MarketRecord]) -> list[ScoredMarket]:
        scored: list[ScoredMarket] = []
        for record in records:
            liquidity_penalty = 1.0 / (1.0 + record.liquidity / 10_000.0)
            momentum = (
                0.50 * record.one_hour_price_change
                + 0.30 * record.one_week_price_change
                + 0.15 * record.one_month_price_change
                + 0.05 * record.one_year_price_change
            )
            volume_signal = min(1.0, max(0.0, record.volume_24h / 100_000.0))
            score = (
                self.weights["edge"] * record.odds_edge
                + self.weights["momentum"] * momentum
                + self.weights["volume"] * volume_signal
                + self.weights["liquidity_penalty"] * liquidity_penalty
            )
            scored.append(
                ScoredMarket(
                    market_id=record.market_id,
                    token_id=record.token_id,
                    reference_price=record.reference_price,
                    score=score,
                    probability=record.probability,
                    liquidity=record.liquidity,
                    edge_component=record.odds_edge,
                    momentum_component=momentum,
                    volume_component=volume_signal,
                    liquidity_penalty_component=liquidity_penalty,
                )
            )
        return sorted(scored, key=lambda item: item.score, reverse=True)

