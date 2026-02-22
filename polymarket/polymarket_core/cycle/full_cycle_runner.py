from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from polymarket_core.backtest.scenario_backtester import BacktestSummary, ScenarioBacktester
from polymarket_core.config import PipelineConfig
from polymarket_core.pipeline.e2e_pipeline import E2EPipeline
from polymarket_core.pipeline.research_pipeline import ResearchPipeline
from polymarket_core.storage.cycle_store import CycleStore


@dataclass(frozen=True)
class CycleDecision:
    approved: bool
    reason: str


@dataclass(frozen=True)
class FullCycleResult:
    approved: bool
    decision_reason: str
    research_expected_return: float
    backtest: BacktestSummary
    executed: bool
    e2e_artifact: str | None
    cycle_artifact: str


class FullCycleRunner:
    """
    Full-cycle pipeline:
    1) research
    2) backtest robustness gate
    3) optional execution
    4) persisted cycle artifact
    """

    def __init__(self, config: PipelineConfig) -> None:
        self.config = config
        self.research = ResearchPipeline(config=config)
        self.backtester = ScenarioBacktester(self.research)
        self.store = CycleStore(config.artifacts_dir)

    def run(
        self,
        *,
        mode: str = "paper",
        confirm_live: bool = False,
        auto_execute: bool = True,
    ) -> FullCycleResult:
        _positions, report = self.research.run()
        backtest = self.backtester.run(
            scenarios=self.config.cycle_backtest_scenarios,
            shock=self.config.cycle_backtest_shock,
        )
        decision = self._decide(backtest)

        executed = False
        e2e_artifact: str | None = None
        if auto_execute and decision.approved:
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
                live_max_orders=self.config.live_max_orders,
                live_min_edge=self.config.live_min_edge,
                cycle_backtest_scenarios=self.config.cycle_backtest_scenarios,
                cycle_backtest_shock=self.config.cycle_backtest_shock,
                cycle_min_avg_return=self.config.cycle_min_avg_return,
                cycle_min_worst_return=self.config.cycle_min_worst_return,
            )
            e2e = E2EPipeline(config=runtime, confirm_live=confirm_live).run()
            executed = True
            e2e_artifact = str(e2e.artifact_path)

        cycle_payload = {
            "mode": mode,
            "approved": decision.approved,
            "decision_reason": decision.reason,
            "research_expected_return": report.expected_return,
            "backtest": asdict(backtest),
            "executed": executed,
            "e2e_artifact": e2e_artifact,
        }
        cycle_path = self.store.save_cycle(cycle_payload)
        return FullCycleResult(
            approved=decision.approved,
            decision_reason=decision.reason,
            research_expected_return=report.expected_return,
            backtest=backtest,
            executed=executed,
            e2e_artifact=e2e_artifact,
            cycle_artifact=str(cycle_path),
        )

    def _decide(self, backtest: BacktestSummary) -> CycleDecision:
        if backtest.avg_expected_return < self.config.cycle_min_avg_return:
            return CycleDecision(
                approved=False,
                reason=(
                    "Rejected: avg backtest return below threshold "
                    f"({backtest.avg_expected_return:.4f} < {self.config.cycle_min_avg_return:.4f})"
                ),
            )
        if backtest.min_expected_return < self.config.cycle_min_worst_return:
            return CycleDecision(
                approved=False,
                reason=(
                    "Rejected: worst-case backtest return below threshold "
                    f"({backtest.min_expected_return:.4f} < {self.config.cycle_min_worst_return:.4f})"
                ),
            )
        return CycleDecision(approved=True, reason="Approved by backtest risk gate.")

