from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from typing import Any, Protocol

from polymarket_core.backtest.scenario_backtester import ScenarioBacktester
from polymarket_core.config import PipelineConfig
from polymarket_core.cycle.full_cycle_runner import FullCycleRunner
from polymarket_core.pipeline.e2e_pipeline import E2EPipeline
from polymarket_core.pipeline.research_pipeline import ResearchPipeline


class AgentTool(Protocol):
    name: str
    description: str

    def run(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute tool and return JSON-serializable payload."""


class MarketResearchTool:
    name = "market_research"
    description = "Analyze current opportunities and return top-ranked positions."

    def __init__(self, config: PipelineConfig) -> None:
        self.pipeline = ResearchPipeline(config=config)

    def run(self, params: dict[str, Any]) -> dict[str, Any]:
        top_k = int(params.get("top_k", 5))
        positions, report = self.pipeline.run()
        rows = [
            {
                "market_id": item.market_id,
                "token_id": item.token_id,
                "weight": round(item.weight, 6),
                "expected_edge": round(item.expected_edge, 6),
            }
            for item in positions[: max(1, top_k)]
        ]
        return {
            "top_positions": rows,
            "gross_exposure": round(report.gross_exposure, 6),
            "expected_return": round(report.expected_return, 6),
        }


class BacktestTool:
    name = "backtest"
    description = "Run scenario-based backtest for robustness checks."

    def __init__(self, config: PipelineConfig) -> None:
        self.backtester = ScenarioBacktester(ResearchPipeline(config=config))

    def run(self, params: dict[str, Any]) -> dict[str, Any]:
        scenarios = int(params.get("scenarios", 50))
        shock = float(params.get("shock", 0.20))
        summary = self.backtester.run(scenarios=scenarios, shock=shock)
        return asdict(summary)


class E2EExecutionTool:
    name = "run_e2e"
    description = "Run E2E pipeline (paper by default) and persist artifacts."

    def __init__(self, config: PipelineConfig) -> None:
        self.config = config

    def run(self, params: dict[str, Any]) -> dict[str, Any]:
        mode = str(params.get("mode", "paper")).lower()
        confirm_live = bool(params.get("confirm_live", False))
        runtime = PipelineConfig(
            lookback=self.config.lookback,
            min_liquidity=self.config.min_liquidity,
            max_position=self.config.max_position,
            signal_threshold=self.config.signal_threshold,
            credentials_path=self.config.credentials_path,
            artifacts_dir=self.config.artifacts_dir,
            initial_capital_usd=self.config.initial_capital_usd,
            execution_mode=mode,
            clob_host=self.config.clob_host,
            clob_chain_id=self.config.clob_chain_id,
            live_max_orders=int(params.get("max_orders", self.config.live_max_orders)),
            live_min_edge=float(params.get("min_edge", self.config.live_min_edge)),
        )
        result = E2EPipeline(config=runtime, confirm_live=confirm_live).run()
        payload = json.loads(Path(result.artifact_path).read_text(encoding="utf-8"))
        return {
            "mode": mode,
            "adapter": result.adapter,
            "positions": len(result.positions),
            "orders": len(result.orders),
            "expected_return": round(result.report.expected_return, 6),
            "artifact_path": str(result.artifact_path),
            "html_report": payload.get("html_report", ""),
        }


class FullCycleTool:
    name = "full_cycle"
    description = (
        "Run full cycle: research, backtest gate, then optional execution and cycle artifact."
    )

    def __init__(self, config: PipelineConfig) -> None:
        self.config = config

    def run(self, params: dict[str, Any]) -> dict[str, Any]:
        mode = str(params.get("mode", "paper")).lower()
        confirm_live = bool(params.get("confirm_live", False))
        auto_execute = bool(params.get("auto_execute", True))
        runtime = PipelineConfig(
            lookback=self.config.lookback,
            min_liquidity=self.config.min_liquidity,
            max_position=self.config.max_position,
            signal_threshold=self.config.signal_threshold,
            credentials_path=self.config.credentials_path,
            artifacts_dir=self.config.artifacts_dir,
            initial_capital_usd=self.config.initial_capital_usd,
            execution_mode=mode,
            clob_host=self.config.clob_host,
            clob_chain_id=self.config.clob_chain_id,
            live_max_orders=int(params.get("max_orders", self.config.live_max_orders)),
            live_min_edge=float(params.get("min_edge", self.config.live_min_edge)),
            cycle_backtest_scenarios=int(
                params.get("backtest_scenarios", self.config.cycle_backtest_scenarios)
            ),
            cycle_backtest_shock=float(
                params.get("backtest_shock", self.config.cycle_backtest_shock)
            ),
            cycle_min_avg_return=float(
                params.get("min_avg_return", self.config.cycle_min_avg_return)
            ),
            cycle_min_worst_return=float(
                params.get("min_worst_return", self.config.cycle_min_worst_return)
            ),
        )
        cycle = FullCycleRunner(runtime).run(
            mode=mode,
            confirm_live=confirm_live,
            auto_execute=auto_execute,
        )
        cycle_payload = json.loads(Path(cycle.cycle_artifact).read_text(encoding="utf-8"))
        return {
            "approved": cycle.approved,
            "decision_reason": cycle.decision_reason,
            "research_expected_return": round(cycle.research_expected_return, 6),
            "backtest": asdict(cycle.backtest),
            "executed": cycle.executed,
            "e2e_artifact": cycle.e2e_artifact,
            "cycle_artifact": cycle.cycle_artifact,
            "cycle_html_report": cycle_payload.get("html_report", ""),
        }


def default_tools(config: PipelineConfig) -> list[AgentTool]:
    return [
        MarketResearchTool(config),
        BacktestTool(config),
        E2EExecutionTool(config),
        FullCycleTool(config),
    ]

