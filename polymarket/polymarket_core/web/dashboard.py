from __future__ import annotations

import json
import logging
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from polymarket_core.alpha.factors import FactorEngine, ScoredMarket
from polymarket_core.config import PipelineConfig
from polymarket_core.engine.simulator import PaperSimulator
from polymarket_core.pipeline.research_pipeline import ResearchPipeline
from polymarket_core.portfolio.risk import PositionIntent


def create_app(base_config: PipelineConfig | None = None) -> Flask:
    config = base_config or PipelineConfig(force_real_data=True)
    template_dir = Path(__file__).resolve().parents[2] / "web" / "templates"
    app = Flask(__name__, template_folder=str(template_dir))
    app.logger.setLevel(logging.INFO)
    build_id = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")

    @app.get("/")
    def dashboard():
        return render_template("dashboard.html", build_id=build_id)

    @app.after_request
    def disable_cache(response):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    @app.get("/api/markets")
    def api_markets():
        limit = _safe_int(request.args.get("limit", "80"), 80, minimum=1, maximum=400)
        offset = _safe_int(request.args.get("offset", "0"), 0, minimum=0, maximum=200000)
        category = str(request.args.get("category", "all")).strip().lower()
        search = str(request.args.get("search", "")).strip().lower()

        pipeline = ResearchPipeline(config=config)
        all_records = pipeline.ingestion.load()
        categories = _category_counts(all_records)
        rows = _filter_records(all_records, category=category, search=search)
        total_count = len(rows)
        rows = sorted(rows, key=lambda item: item.liquidity, reverse=True)
        paged = rows[offset : offset + limit]
        has_more = (offset + len(paged)) < total_count

        return jsonify(
            {
                "adapter": pipeline.adapter.__class__.__name__,
                "data_source": "gamma-api.polymarket.com",
                "is_mock": False,
                "real_data_only": True,
                "count": len(paged),
                "total_count": total_count,
                "offset": offset,
                "limit": limit,
                "has_more": has_more,
                "categories": categories,
                "markets": [
                    {
                        "market_id": item.market_id,
                        "question": item.question,
                        "event_title": item.event_title,
                        "category": item.category,
                        "token_id": item.token_id,
                        "expiration_iso": item.expiration_iso,
                        "cashout_iso": item.cashout_iso,
                        "probability": item.probability,
                        "liquidity": item.liquidity,
                        "volume_24h": item.volume_24h,
                        "odds_edge": item.odds_edge,
                    }
                    for item in paged
                ],
            }
        )

    @app.post("/api/backtest")
    def api_backtest():
        payload = request.get_json(silent=True) or {}
        runtime = PipelineConfig(
            lookback=config.lookback,
            min_liquidity=_safe_float(payload.get("min_liquidity", config.min_liquidity), config.min_liquidity),
            max_position=_safe_float(payload.get("max_position", config.max_position), config.max_position),
            signal_threshold=_safe_float(
                payload.get("signal_threshold", config.signal_threshold), config.signal_threshold
            ),
            credentials_path=config.credentials_path,
            artifacts_dir=config.artifacts_dir,
            initial_capital_usd=_safe_float(
                payload.get("initial_capital_usd", config.initial_capital_usd), config.initial_capital_usd
            ),
            execution_mode="paper",
            clob_host=config.clob_host,
            clob_chain_id=config.clob_chain_id,
            live_max_orders=config.live_max_orders,
            live_min_edge=config.live_min_edge,
            force_real_data=config.force_real_data,
            cycle_backtest_scenarios=config.cycle_backtest_scenarios,
            cycle_backtest_shock=config.cycle_backtest_shock,
            cycle_min_avg_return=config.cycle_min_avg_return,
            cycle_min_worst_return=config.cycle_min_worst_return,
        )
        scenarios = _safe_int(payload.get("scenarios", 80), 80, minimum=10, maximum=1000)
        shock = _safe_float(payload.get("shock", 0.25), 0.25)
        seed = _safe_int(payload.get("seed", 7), 7, minimum=0, maximum=999999)
        timeframe_days = _safe_int(payload.get("timeframe_days", 30), 30, minimum=1, maximum=3650)
        bar_interval_hours = _safe_int(
            payload.get("bar_interval_hours", 24), 24, minimum=1, maximum=168
        )
        curve_steps = max(2, min(2000, int((timeframe_days * 24) / bar_interval_hours)))
        category = str(payload.get("category", "all")).strip().lower()
        search = str(payload.get("search", "")).strip().lower()
        selected_market_ids = payload.get("selected_market_ids", [])
        selected_ids = {str(item) for item in selected_market_ids if str(item).strip()}
        strategy_name = str(payload.get("strategy_name", "balanced")).strip().lower()
        strategy_weights = _parse_strategy_weights(payload.get("strategy_weights"))
        market_neutral = bool(payload.get("market_neutral", True))
        replay_mode = str(payload.get("replay_mode", "settlement_only")).strip().lower()
        if replay_mode not in {"settlement_only", "mark_to_market"}:
            replay_mode = "settlement_only"

        pipeline = ResearchPipeline(config=runtime)
        all_records = pipeline.ingestion.load()
        filtered = _filter_records(all_records, category=category, search=search)
        if selected_ids:
            filtered = [item for item in filtered if item.market_id in selected_ids]

        positions, report, scored, resolved_strategy_name, resolved_weights, selection_meta = _run_research_for_records(
            runtime,
            filtered,
            strategy_name=strategy_name,
            strategy_weights=strategy_weights,
            market_neutral=market_neutral,
        )
        backtest = _real_backtest_from_market_changes(
            positions=positions,
            records=filtered,
            initial_capital_usd=runtime.initial_capital_usd,
            timeframe_days=timeframe_days,
            replay_mode=replay_mode,
        )
        trades = _trade_summary(
            positions,
            runtime.initial_capital_usd,
            filtered,
            timeframe_days=timeframe_days,
            replay_mode=replay_mode,
        )
        curve = _real_pnl_curve_from_market_changes(
            positions=positions,
            records=filtered,
            initial_capital_usd=runtime.initial_capital_usd,
            timeframe_days=timeframe_days,
            requested_steps=curve_steps,
            replay_mode=replay_mode,
        )
        metric_summary = _metric_summary(
            positions=positions,
            curve=curve,
            initial_capital_usd=runtime.initial_capital_usd,
        )
        trace = _build_trace(
            positions=positions,
            trades=trades,
            metrics=metric_summary,
            timeframe_days=timeframe_days,
            bar_interval_hours=bar_interval_hours,
            category=category,
            search=search,
            selected_count=len(selected_ids),
            universe_size=len(filtered),
            strategy_name=resolved_strategy_name,
            market_neutral=market_neutral,
            selection_meta=selection_meta,
            replay_mode=replay_mode,
        )
        app.logger.info("backtest_trace=%s", json.dumps(trace, separators=(",", ":")))
        print(f"backtest_trace={json.dumps(trace, separators=(',', ':'))}", flush=True)
        return jsonify(
            {
                "adapter": pipeline.adapter.__class__.__name__,
                "data_source": "gamma-api.polymarket.com",
                "is_mock": False,
                "real_data_only": True,
                "selection": {
                    "selected_count": len(selected_ids),
                    "universe_size": len(filtered),
                    "category": category,
                    "search": search,
                },
                "timeframe": {
                    "days": timeframe_days,
                    "bar_interval_hours": bar_interval_hours,
                    "curve_steps": curve_steps,
                },
                "backtest_mode": "market_replay_real",
                "replay_mode": replay_mode,
                "report": asdict(report),
                "backtest": backtest,
                "trade_summary": trades,
                "exposure": _exposure_summary(positions),
                "pnl_curve": curve,
                "metrics": metric_summary,
                "trace": trace,
                "strategy": {
                    "name": resolved_strategy_name,
                    "weights": resolved_weights,
                    "market_neutral": market_neutral,
                },
                "strategy_output": {
                    "count": len(scored),
                    "rows": _strategy_rows(scored, filtered),
                },
            }
        )

    return app


def _run_research_for_records(
    config: PipelineConfig,
    records,
    *,
    strategy_name: str,
    strategy_weights: dict[str, float] | None,
    market_neutral: bool,
):
    subset = [item for item in records if item.liquidity >= config.min_liquidity]
    factor = FactorEngine(strategy_name=strategy_name, custom_weights=strategy_weights)
    scored = factor.score(subset)
    picks = [item for item in scored if abs(item.score) >= config.signal_threshold]
    picks_before_pairing_count = len(picks)
    picks_before_pairing_long = sum(1 for item in picks if item.score >= 0)
    picks_before_pairing_short = sum(1 for item in picks if item.score < 0)
    if market_neutral:
        long_candidates = [item for item in picks if item.score >= 0]
        short_candidates = [item for item in picks if item.score < 0]
        pair_count = min(len(long_candidates), len(short_candidates))
        if pair_count > 0:
            long_selected = sorted(long_candidates, key=lambda item: abs(item.score), reverse=True)[:pair_count]
            short_selected = sorted(short_candidates, key=lambda item: abs(item.score), reverse=True)[:pair_count]
            picks = long_selected + short_selected
    gross = sum(abs(item.score) for item in picks)
    if gross <= 0:
        positions: list[PositionIntent] = []
    else:
        positions = []
        for item in picks:
            weight = min(abs(item.score) / gross, config.max_position)
            positions.append(
                PositionIntent(
                    market_id=item.market_id,
                    token_id=item.token_id,
                    reference_price=item.reference_price,
                    weight=weight,
                    expected_edge=item.score,
                )
            )
        if market_neutral:
            long_gross = sum(p.weight for p in positions if p.expected_edge >= 0)
            short_gross = sum(p.weight for p in positions if p.expected_edge < 0)
            if long_gross > 0 and short_gross > 0:
                long_scale = min(1.0, short_gross / long_gross)
                short_scale = min(1.0, long_gross / short_gross)
                balanced: list[PositionIntent] = []
                for p in positions:
                    scale = long_scale if p.expected_edge >= 0 else short_scale
                    balanced.append(
                        PositionIntent(
                            market_id=p.market_id,
                            token_id=p.token_id,
                            reference_price=p.reference_price,
                            weight=p.weight * scale,
                            expected_edge=p.expected_edge,
                        )
                    )
                positions = balanced
    report = PaperSimulator().run(positions)
    selection_meta = {
        "subset_count": len(subset),
        "scored_count": len(scored),
        "picks_before_pairing_count": picks_before_pairing_count,
        "picks_before_pairing_long": picks_before_pairing_long,
        "picks_before_pairing_short": picks_before_pairing_short,
    }
    return positions, report, scored, factor.strategy_name, factor.weights, selection_meta


def _filter_records(records, *, category: str, search: str):
    rows = records
    if category and category != "all":
        rows = [item for item in rows if item.category.lower() == category]
    if search:
        rows = [
            item
            for item in rows
            if search in item.question.lower()
            or search in item.event_title.lower()
            or search in item.category.lower()
            or search in item.market_id.lower()
        ]
    return rows


def _category_counts(records) -> list[dict]:
    counts: dict[str, int] = {"all": len(records)}
    for item in records:
        key = item.category.lower() if item.category else "all"
        counts[key] = counts.get(key, 0) + 1
    return [{"name": key, "count": value} for key, value in sorted(counts.items())]


def _parse_strategy_weights(payload) -> dict[str, float] | None:
    if payload is None:
        return None
    if not isinstance(payload, dict):
        return None
    out: dict[str, float] = {}
    for key in ("edge", "momentum", "volume", "liquidity_penalty"):
        value = payload.get(key)
        if value is None:
            continue
        try:
            out[key] = float(value)
        except (TypeError, ValueError):
            continue
    return out or None


def _strategy_rows(scored: list[ScoredMarket], records) -> list[dict]:
    lookup = {item.market_id: item for item in records}
    rows: list[dict] = []
    for item in scored[:200]:
        info = lookup.get(item.market_id)
        rows.append(
            {
                "market_id": item.market_id,
                "question": info.question if info else item.market_id,
                "category": info.category if info else "unknown",
                "score": item.score,
                "edge": item.edge_component,
                "momentum": item.momentum_component,
                "volume": item.volume_component,
                "liquidity_penalty": item.liquidity_penalty_component,
            }
        )
    return rows


def _trade_summary(
    positions,
    capital: float,
    records,
    *,
    timeframe_days: int,
    replay_mode: str,
) -> dict:
    metadata = {item.market_id: item for item in records}
    rows = []
    expected_pnl_total = 0.0
    replay_pnl_total = 0.0
    total_notional = 0.0
    total_hours = max(1.0, timeframe_days * 24.0)
    now = datetime.now(UTC)
    for item in positions:
        info = metadata.get(item.market_id)
        notional = round(item.weight * capital, 2)
        side = "BUY_YES" if item.expected_edge >= 0 else "BUY_NO"
        signal_score = round(abs(item.expected_edge), 6)
        weighted_signal = item.weight * abs(item.expected_edge)
        replay_pnl = 0.0
        if info is not None:
            replay_pnl = round(
                _position_replay_pnl(
                    position=item,
                    info=info,
                    initial_capital_usd=capital,
                    elapsed_hours=total_hours,
                    total_hours=total_hours,
                    now=now,
                    replay_mode=replay_mode,
                ),
                2,
            )
        expected_pnl_total += weighted_signal
        replay_pnl_total += replay_pnl
        total_notional += notional
        rows.append(
            {
                "market_id": item.market_id,
                "question": info.question if info else item.market_id,
                "category": info.category if info else "unknown",
                "token_id": item.token_id,
                "expiration_iso": info.expiration_iso if info else "",
                "cashout_iso": info.cashout_iso if info else "",
                "side": side,
                "weight": item.weight,
                "expected_edge": item.expected_edge,
                "notional_usd": notional,
                "signal_score": signal_score,
                # Backward-compatible field name retained for older UI consumers.
                "model_pnl_usd": signal_score,
                "replay_pnl_usd": replay_pnl,
                "model_pnl_class": "score",
                "pnl_class": "profit" if replay_pnl > 0 else ("loss" if replay_pnl < 0 else "flat"),
            }
        )
    return {
        "total_notional_usd": round(total_notional, 2),
        "expected_model_pnl_usd": round(expected_pnl_total, 6),
        "replay_pnl_usd": round(replay_pnl_total, 2),
        "trades": rows,
    }


def _exposure_summary(positions) -> dict:
    long_gross = sum(item.weight for item in positions if item.expected_edge >= 0)
    short_gross = sum(item.weight for item in positions if item.expected_edge < 0)
    gross = long_gross + short_gross
    net = long_gross - short_gross
    return {
        "gross_long": long_gross,
        "gross_short": short_gross,
        "gross_total": gross,
        "net": net,
        "net_pct_gross": (net / gross) if gross > 0 else 0.0,
        "long_count": sum(1 for item in positions if item.expected_edge >= 0),
        "short_count": sum(1 for item in positions if item.expected_edge < 0),
    }


def _metric_summary(positions, curve: list[dict], initial_capital_usd: float) -> dict:
    model_expected_return = sum(item.weight * abs(item.expected_edge) for item in positions)
    model_signal_score = model_expected_return
    final_equity = curve[-1]["equity"] if curve else initial_capital_usd
    replay_pnl_usd = final_equity - initial_capital_usd
    replay_return = replay_pnl_usd / max(initial_capital_usd, 1e-9)
    return {
        "model_expected_return": model_expected_return,
        "model_signal_score": model_signal_score,
        # Backward-compatible key retained, now explicitly score-like (unitless).
        "model_expected_pnl_usd": model_signal_score,
        "replay_final_pnl_usd": replay_pnl_usd,
        "replay_final_return": replay_return,
        "report_expected_return_signed": sum(item.weight * item.expected_edge for item in positions),
    }


def _build_trace(
    *,
    positions,
    trades: dict,
    metrics: dict,
    timeframe_days: int,
    bar_interval_hours: int,
    category: str,
    search: str,
    selected_count: int,
    universe_size: int,
    strategy_name: str,
    market_neutral: bool,
    selection_meta: dict,
    replay_mode: str,
) -> dict:
    rows = trades.get("trades", [])
    replay_sorted = sorted(rows, key=lambda item: float(item.get("replay_pnl_usd", 0.0)))
    worst = replay_sorted[:3]
    best = replay_sorted[-3:]
    return {
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "inputs": {
            "timeframe_days": timeframe_days,
            "bar_interval_hours": bar_interval_hours,
            "category": category,
            "search": search,
            "selected_count": selected_count,
            "universe_size": universe_size,
            "strategy_name": strategy_name,
            "market_neutral": market_neutral,
            "replay_mode": replay_mode,
        },
        "selection_meta": selection_meta,
        "positions": {
            "count": len(positions),
            "long_count": sum(1 for p in positions if p.expected_edge >= 0),
            "short_count": sum(1 for p in positions if p.expected_edge < 0),
            "gross_weight": sum(float(p.weight) for p in positions),
        },
        "totals": {
            "model_expected_return": metrics.get("model_expected_return", 0.0),
            "model_signal_score": metrics.get("model_signal_score", 0.0),
            "model_expected_pnl_usd": metrics.get("model_expected_pnl_usd", 0.0),
            "replay_final_return": metrics.get("replay_final_return", 0.0),
            "replay_final_pnl_usd": metrics.get("replay_final_pnl_usd", 0.0),
            "trade_summary_replay_pnl_usd": trades.get("replay_pnl_usd", 0.0),
            "replay_reconcile_error_usd": round(
                float(metrics.get("replay_final_pnl_usd", 0.0))
                - float(trades.get("replay_pnl_usd", 0.0)),
                6,
            ),
        },
        "top_worst_replay_trades": [
            {
                "market_id": item.get("market_id"),
                "question": item.get("question"),
                "side": item.get("side"),
                "replay_pnl_usd": item.get("replay_pnl_usd"),
            }
            for item in worst
        ],
        "top_best_replay_trades": [
            {
                "market_id": item.get("market_id"),
                "question": item.get("question"),
                "side": item.get("side"),
                "replay_pnl_usd": item.get("replay_pnl_usd"),
            }
            for item in reversed(best)
        ],
    }


def _real_pnl_curve_from_market_changes(
    *,
    positions,
    records,
    initial_capital_usd: float,
    timeframe_days: int,
    requested_steps: int,
    replay_mode: str,
) -> list[dict]:
    meta = {item.market_id: item for item in records}
    total_hours = max(1.0, timeframe_days * 24.0)
    steps = max(2, int(requested_steps))
    now = datetime.now(UTC)
    equity = initial_capital_usd
    curve = [{"step": 0, "label": "now", "equity": round(equity, 2), "pnl": 0.0}]
    previous_total_pnl = 0.0
    for idx in range(1, steps + 1):
        elapsed_hours = total_hours * (idx / steps)
        cumulative_total_pnl = 0.0
        for position in positions:
            info = meta.get(position.market_id)
            if info is None:
                continue
            cumulative_total_pnl += _position_replay_pnl(
                position=position,
                info=info,
                initial_capital_usd=initial_capital_usd,
                elapsed_hours=elapsed_hours,
                total_hours=total_hours,
                now=now,
                replay_mode=replay_mode,
            )
        pnl = cumulative_total_pnl - previous_total_pnl
        previous_total_pnl = cumulative_total_pnl
        equity = initial_capital_usd + cumulative_total_pnl
        curve.append(
            {
                "step": idx,
                "label": f"t{idx}",
                "equity": round(equity, 2),
                "pnl": round(pnl, 2),
            }
        )
    return curve


def _real_backtest_from_market_changes(
    *,
    positions,
    records,
    initial_capital_usd: float,
    timeframe_days: int,
    replay_mode: str,
) -> dict:
    curve = _real_pnl_curve_from_market_changes(
        positions=positions,
        records=records,
        initial_capital_usd=initial_capital_usd,
        timeframe_days=timeframe_days,
        requested_steps=999,
        replay_mode=replay_mode,
    )
    rets = []
    for row in curve[1:]:
        ret = (row["equity"] - initial_capital_usd) / max(initial_capital_usd, 1e-9)
        rets.append(ret)
    if not rets:
        return {"scenarios": 0, "avg_expected_return": 0.0, "min_expected_return": 0.0, "max_expected_return": 0.0}
    return {
        "scenarios": len(rets),
        "avg_expected_return": sum(rets) / len(rets),
        "min_expected_return": min(rets),
        "max_expected_return": max(rets),
    }


def _anchor_points(timeframe_days: int) -> list[tuple[str, str]]:
    anchors: list[tuple[str, str]] = [("1h", "one_hour_price_change")]
    if timeframe_days >= 7:
        anchors.append(("1w", "one_week_price_change"))
    if timeframe_days >= 30:
        anchors.append(("1m", "one_month_price_change"))
    if timeframe_days >= 365:
        anchors.append(("1y", "one_year_price_change"))
    return anchors


def _interpolated_price_change(info, elapsed_hours: float, total_hours: float) -> float:
    max_horizon = max(1.0, min(total_hours, 8760.0))
    target = max(0.0, min(elapsed_hours, max_horizon))
    points = [(0.0, 0.0), (1.0, float(getattr(info, "one_hour_price_change", 0.0)))]
    if max_horizon >= 168.0:
        points.append((168.0, float(getattr(info, "one_week_price_change", 0.0))))
    if max_horizon >= 720.0:
        points.append((720.0, float(getattr(info, "one_month_price_change", 0.0))))
    if max_horizon >= 8760.0:
        points.append((8760.0, float(getattr(info, "one_year_price_change", 0.0))))
    points = sorted(points, key=lambda item: item[0])
    if target <= points[0][0]:
        return points[0][1]
    if target >= points[-1][0]:
        return points[-1][1]
    for idx in range(1, len(points)):
        left_h, left_v = points[idx - 1]
        right_h, right_v = points[idx]
        if left_h <= target <= right_h:
            span = max(1e-9, right_h - left_h)
            ratio = (target - left_h) / span
            # Smooth interpolation (not linear) avoids unrealistic equal step deltas.
            smooth_ratio = ratio * ratio * (3.0 - 2.0 * ratio)
            return left_v + (right_v - left_v) * smooth_ratio
    return points[-1][1]


def _hours_until_expiry(expiration_iso: str, now: datetime) -> float:
    expiry = _parse_iso_datetime(expiration_iso)
    if expiry is None:
        return 24.0
    return max(1.0, (expiry - now).total_seconds() / 3600.0)


def _position_replay_pnl(
    *,
    position: PositionIntent,
    info,
    initial_capital_usd: float,
    elapsed_hours: float,
    total_hours: float,
    now: datetime,
    replay_mode: str,
) -> float:
    direction = 1.0 if position.expected_edge >= 0 else -1.0
    notional = position.weight * initial_capital_usd
    expiry_hours = _hours_until_expiry(info.expiration_iso, now)
    effective_hours = min(total_hours, max(1.0, expiry_hours))
    mark_hours = min(max(0.0, elapsed_hours), effective_hours)
    if replay_mode == "settlement_only":
        if effective_hours > total_hours:
            return 0.0
        if elapsed_hours < effective_hours:
            return 0.0
        mark_hours = effective_hours
    delta_price = _interpolated_price_change(info, mark_hours, total_hours)
    return notional * direction * delta_price


def _parse_iso_datetime(value: str) -> datetime | None:
    text = (value or "").strip()
    if not text:
        return None
    candidate = text
    if len(candidate) == 10:
        candidate = f"{candidate}T00:00:00+00:00"
    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _safe_int(value, fallback: int, *, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return fallback
    return max(minimum, min(maximum, parsed))


def _safe_float(value, fallback: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback

