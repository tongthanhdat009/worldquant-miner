from dataclasses import dataclass
from pathlib import Path

from polymarket_core.adapters.credentials import load_polymarket_credentials
from polymarket_core.config import PipelineConfig
from polymarket_core.engine.simulator import SimulationReport
from polymarket_core.execution.live_executor import LiveExecutionConfig, LiveExecutor
from polymarket_core.execution.paper_executor import PaperExecutor
from polymarket_core.execution.types import ExecutedOrder
from polymarket_core.pipeline.research_pipeline import ResearchPipeline
from polymarket_core.portfolio.risk import PositionIntent
from polymarket_core.storage.run_store import RunStore


@dataclass(frozen=True)
class E2ERunResult:
    adapter: str
    positions: list[PositionIntent]
    orders: list[ExecutedOrder]
    report: SimulationReport
    artifact_path: Path


class E2EPipeline:
    def __init__(
        self,
        config: PipelineConfig | None = None,
        *,
        confirm_live: bool = False,
    ) -> None:
        self.config = config or PipelineConfig()
        self.research = ResearchPipeline(config=self.config)
        self.executor = self._build_executor(confirm_live=confirm_live)
        self.run_store = RunStore(artifacts_dir=self.config.artifacts_dir)

    def run(self) -> E2ERunResult:
        positions, report = self.research.run()
        orders = self.executor.execute(positions)
        artifact_path = self.run_store.save_run(
            adapter_name=self.research.adapter.__class__.__name__,
            positions=positions,
            orders=orders,
            report=report,
        )
        return E2ERunResult(
            adapter=self.research.adapter.__class__.__name__,
            positions=positions,
            orders=orders,
            report=report,
            artifact_path=artifact_path,
        )

    def _build_executor(self, *, confirm_live: bool):
        if self.config.execution_mode.lower() != "live":
            return PaperExecutor(initial_capital_usd=self.config.initial_capital_usd)
        if not confirm_live:
            raise RuntimeError(
                "Live mode requested but not confirmed. Re-run with --confirm-live."
            )
        credentials = load_polymarket_credentials(self.config.credentials_path)
        if credentials is None:
            raise RuntimeError("Live mode requires credentials, but none were found.")
        return LiveExecutor(
            credentials=credentials,
            config=LiveExecutionConfig(
                host=self.config.clob_host,
                chain_id=self.config.clob_chain_id,
                max_orders=self.config.live_max_orders,
                min_edge=self.config.live_min_edge,
            ),
            initial_capital_usd=self.config.initial_capital_usd,
        )
