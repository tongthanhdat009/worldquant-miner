from __future__ import annotations

from datetime import UTC, datetime
from html import escape
from pathlib import Path


class HtmlReportRenderer:
    def render_run_report(self, payload: dict) -> str:
        orders = payload.get("orders", [])
        total_notional = sum(_as_float(item.get("notional_usd")) for item in orders)
        expected_pnl_values = [
            _as_float(item.get("notional_usd")) * _as_float(item.get("expected_edge"))
            for item in orders
        ]
        expected_pnl = sum(expected_pnl_values)
        fill_count = sum(1 for item in orders if str(item.get("status", "")).upper() == "FILLED")
        realized_pnl = 0.0  # Paper mode does not close positions yet; no realized P/L.
        positive_pnl = sum(value for value in expected_pnl_values if value > 0)
        negative_pnl = sum(value for value in expected_pnl_values if value < 0)
        profitable_trades = sum(1 for value in expected_pnl_values if value > 0)
        losing_trades = sum(1 for value in expected_pnl_values if value < 0)
        trade_count = len(expected_pnl_values)
        hit_rate = (profitable_trades / trade_count * 100.0) if trade_count else 0.0

        order_rows = "\n".join(
            _row(
                [
                    item.get("market_id", ""),
                    item.get("token_id", ""),
                    item.get("side", ""),
                    f"{_as_float(item.get('notional_usd')):.2f}",
                    f"{_as_float(item.get('expected_edge')):.6f}",
                    f"{(_as_float(item.get('notional_usd')) * _as_float(item.get('expected_edge'))):.2f}",
                    _pnl_label(
                        _as_float(item.get("notional_usd")) * _as_float(item.get("expected_edge"))
                    ),
                    item.get("status", ""),
                    item.get("venue_order_id", "") or "",
                ]
            )
            for item in orders
        )
        if not order_rows:
            order_rows = _row(["-", "-", "-", "0.00", "0.000000", "0.00", "flat", "NONE", ""])

        return _page(
            title=f"Polymarket Run Report {payload.get('run_id', '')}",
            subtitle=f"Generated at {escape(str(payload.get('timestamp_utc', _now_utc())))}",
            summary_rows=[
                ("Adapter", str(payload.get("adapter", ""))),
                ("Positions", str(payload.get("report", {}).get("positions", 0))),
                ("Gross Exposure", f"{_as_float(payload.get('report', {}).get('gross_exposure')):.6f}"),
                ("Expected Return", f"{_as_float(payload.get('report', {}).get('expected_return')):.6f}"),
                ("Total Notional (USD)", f"{total_notional:.2f}"),
                ("Realized PnL (USD)", f"{realized_pnl:.2f}"),
                ("Unrealized Model PnL (USD)", f"{expected_pnl:.2f}"),
                ("Profit Bucket (USD)", f"{positive_pnl:.2f}"),
                ("Loss Bucket (USD)", f"{negative_pnl:.2f}"),
                ("Filled Orders", str(fill_count)),
                ("Profitable Trades", str(profitable_trades)),
                ("Losing Trades", str(losing_trades)),
                ("Hit Rate", f"{hit_rate:.2f}%"),
            ],
            table_headers=[
                "Market ID",
                "Token ID",
                "Side",
                "Notional USD",
                "Expected Edge",
                "Model PnL USD",
                "P/L Class",
                "Status",
                "Venue Order ID",
            ],
            table_rows=order_rows,
        )

    def render_cycle_report(self, payload: dict) -> str:
        backtest = payload.get("backtest", {})
        return _page(
            title=f"Polymarket Cycle Report {payload.get('cycle_id', '')}",
            subtitle=f"Generated at {escape(str(payload.get('timestamp_utc', _now_utc())))}",
            summary_rows=[
                ("Mode", str(payload.get("mode", ""))),
                ("Approved", str(payload.get("approved", False))),
                ("Decision Reason", str(payload.get("decision_reason", ""))),
                (
                    "Research Expected Return",
                    f"{_as_float(payload.get('research_expected_return')):.6f}",
                ),
                ("Backtest Scenarios", str(backtest.get("scenarios", 0))),
                (
                    "Backtest Avg Return",
                    f"{_as_float(backtest.get('avg_expected_return')):.6f}",
                ),
                (
                    "Backtest Min Return",
                    f"{_as_float(backtest.get('min_expected_return')):.6f}",
                ),
                (
                    "Backtest Max Return",
                    f"{_as_float(backtest.get('max_expected_return')):.6f}",
                ),
                ("Executed", str(payload.get("executed", False))),
                ("Run Artifact", str(payload.get("e2e_artifact", ""))),
            ],
            table_headers=["Key", "Value"],
            table_rows=_row(["Cycle Artifact", str(payload.get("cycle_id", ""))]),
        )

    def write_html(self, *, html_content: str, output_path: Path) -> Path:
        output_path.write_text(html_content, encoding="utf-8")
        return output_path


def _page(
    *,
    title: str,
    subtitle: str,
    summary_rows: list[tuple[str, str]],
    table_headers: list[str],
    table_rows: str,
) -> str:
    summary_html = "\n".join(
        f"<tr><th>{escape(key)}</th><td>{escape(value)}</td></tr>" for key, value in summary_rows
    )
    header_html = "".join(f"<th>{escape(item)}</th>" for item in table_headers)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{escape(title)}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; color: #111; }}
    h1 {{ margin-bottom: 4px; }}
    .subtitle {{ color: #444; margin-bottom: 18px; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 12px; }}
    th, td {{ border: 1px solid #d0d0d0; padding: 8px; text-align: left; font-size: 14px; }}
    th {{ background: #f5f5f5; }}
    .section-title {{ margin-top: 22px; font-size: 18px; }}
    code {{ background: #f0f0f0; padding: 1px 4px; border-radius: 4px; }}
  </style>
</head>
<body>
  <h1>{escape(title)}</h1>
  <div class="subtitle">{escape(subtitle)}</div>
  <div class="section-title">Summary</div>
  <table>
    <tbody>
      {summary_html}
    </tbody>
  </table>
  <div class="section-title">Details</div>
  <table>
    <thead><tr>{header_html}</tr></thead>
    <tbody>
      {table_rows}
    </tbody>
  </table>
</body>
</html>
"""


def _row(values: list[object]) -> str:
    cells = "".join(f"<td>{escape(str(value))}</td>" for value in values)
    return f"<tr>{cells}</tr>"


def _as_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _now_utc() -> str:
    return datetime.now(UTC).isoformat()


def _pnl_label(value: float) -> str:
    if value > 0:
        return "profit"
    if value < 0:
        return "loss"
    return "flat"

