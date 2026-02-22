from pathlib import Path

from polymarket_core.config import PipelineConfig
from polymarket_core.web.dashboard import create_app


def test_dashboard_endpoints() -> None:
    app = create_app(PipelineConfig(credentials_path="missing.txt", force_real_data=False))
    client = app.test_client()

    home = client.get("/")
    assert home.status_code == 200
    assert b"Polymarket Quant Dashboard" in home.data

    markets = client.get("/api/markets?limit=3")
    assert markets.status_code == 200
    payload = markets.get_json()
    assert payload["count"] <= 3
    assert "markets" in payload
    assert "is_mock" in payload

    backtest = client.post(
        "/api/backtest",
        json={
            "scenarios": 20,
            "timeframe_days": 14,
            "bar_interval_hours": 12,
            "shock": 0.2,
            "seed": 11,
            "initial_capital_usd": 10000,
        },
    )
    assert backtest.status_code == 200
    body = backtest.get_json()
    assert "pnl_curve" in body
    assert len(body["pnl_curve"]) >= 2
    assert "trade_summary" in body
    assert "is_mock" in body
    assert body["timeframe"]["days"] == 14
    assert body["timeframe"]["bar_interval_hours"] == 12
    assert body["backtest_mode"] == "market_replay_real"

