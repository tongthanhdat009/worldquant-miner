from __future__ import annotations

from dataclasses import dataclass

from polymarket_core.adapters.credentials import PolymarketCredentials
from polymarket_core.portfolio.risk import PositionIntent

from .types import ExecutedOrder


@dataclass(frozen=True)
class LiveExecutionConfig:
    host: str = "https://clob.polymarket.com"
    chain_id: int = 137
    max_orders: int = 3
    min_edge: float = 0.06
    order_type: str = "FOK"


class LiveExecutor:
    """
    Real order executor using py-clob-client.
    Requires a private key plus API credentials.
    """

    def __init__(
        self,
        *,
        credentials: PolymarketCredentials,
        config: LiveExecutionConfig,
        initial_capital_usd: float,
    ) -> None:
        self.credentials = credentials
        self.config = config
        self.initial_capital_usd = initial_capital_usd
        self._client = self._build_client()

    def execute(self, positions: list[PositionIntent]) -> list[ExecutedOrder]:
        candidates = [
            item for item in positions if item.expected_edge >= self.config.min_edge
        ][: self.config.max_orders]

        orders: list[ExecutedOrder] = []
        for position in candidates:
            notional = round(position.weight * self.initial_capital_usd, 2)
            try:
                signed = self._create_market_order(position, notional)
                posted = self._client.post_order(signed, orderType=self.config.order_type)
                venue_order_id = _extract_order_id(posted)
                orders.append(
                    ExecutedOrder(
                        market_id=position.market_id,
                        token_id=position.token_id,
                        side="BUY",
                        notional_usd=notional,
                        expected_edge=position.expected_edge,
                        status="FILLED" if venue_order_id else "SUBMITTED",
                        venue_order_id=venue_order_id,
                        message="posted-to-clob",
                    )
                )
            except Exception as exc:  # noqa: BLE001
                orders.append(
                    ExecutedOrder(
                        market_id=position.market_id,
                        token_id=position.token_id,
                        side="BUY",
                        notional_usd=notional,
                        expected_edge=position.expected_edge,
                        status="REJECTED",
                        message=str(exc),
                    )
                )
        return orders

    def _build_client(self):
        if not self.credentials.private_key:
            raise RuntimeError("POLYMARKET_PRIVATE_KEY is required for live execution.")
        if not (
            self.credentials.api_key
            and self.credentials.api_secret
            and self.credentials.api_passphrase
        ):
            raise RuntimeError(
                "Live execution requires API key/secret/passphrase credentials."
            )

        from py_clob_client.client import ClobClient
        from py_clob_client.clob_types import ApiCreds

        client = ClobClient(
            host=self.config.host,
            chain_id=self.config.chain_id,
            key=self.credentials.private_key,
            creds=ApiCreds(
                api_key=self.credentials.api_key,
                api_secret=self.credentials.api_secret,
                api_passphrase=self.credentials.api_passphrase,
            ),
            funder=self.credentials.funder,
        )
        return client

    def _create_market_order(self, position: PositionIntent, notional_usd: float):
        from py_clob_client.clob_types import MarketOrderArgs

        return self._client.create_market_order(
            MarketOrderArgs(
                token_id=position.token_id,
                amount=notional_usd,
                side="BUY",
            )
        )


def _extract_order_id(payload: object) -> str | None:
    if isinstance(payload, dict):
        for key in ("orderID", "orderId", "id"):
            value = payload.get(key)
            if value:
                return str(value)
    return None

