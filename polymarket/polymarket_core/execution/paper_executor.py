from polymarket_core.portfolio.risk import PositionIntent
from .types import ExecutedOrder


class PaperExecutor:
    """Simulate order creation without sending any external trade requests."""

    def __init__(self, initial_capital_usd: float) -> None:
        self.initial_capital_usd = initial_capital_usd

    def execute(self, positions: list[PositionIntent]) -> list[ExecutedOrder]:
        orders: list[ExecutedOrder] = []
        for position in positions:
            orders.append(
                ExecutedOrder(
                    market_id=position.market_id,
                    token_id=position.token_id,
                    side="BUY" if position.expected_edge >= 0 else "SELL",
                    notional_usd=round(position.weight * self.initial_capital_usd, 2),
                    expected_edge=position.expected_edge,
                    status="FILLED",
                )
            )
        return orders

