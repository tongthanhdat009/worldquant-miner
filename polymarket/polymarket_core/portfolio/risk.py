from dataclasses import dataclass

from polymarket_core.alpha.factors import ScoredMarket
from polymarket_core.config import PipelineConfig


@dataclass(frozen=True)
class PositionIntent:
    market_id: str
    token_id: str
    reference_price: float
    weight: float
    expected_edge: float


class RiskManager:
    def __init__(self, config: PipelineConfig) -> None:
        self.config = config

    def build_positions(self, scored: list[ScoredMarket]) -> list[PositionIntent]:
        picks = [m for m in scored if m.score >= self.config.signal_threshold]
        if not picks:
            return []

        gross = sum(abs(m.score) for m in picks)
        if gross <= 0:
            return []

        positions: list[PositionIntent] = []
        for market in picks:
            raw_weight = abs(market.score) / gross
            bounded_weight = min(raw_weight, self.config.max_position)
            positions.append(
                PositionIntent(
                    market_id=market.market_id,
                    token_id=market.token_id,
                    reference_price=market.reference_price,
                    weight=bounded_weight,
                    expected_edge=market.score,
                )
            )
        return positions

