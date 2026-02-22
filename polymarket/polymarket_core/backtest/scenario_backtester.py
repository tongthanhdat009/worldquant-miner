from __future__ import annotations

from dataclasses import dataclass
from random import Random
from statistics import mean

from polymarket_core.pipeline.research_pipeline import ResearchPipeline


@dataclass(frozen=True)
class BacktestSummary:
    scenarios: int
    avg_expected_return: float
    min_expected_return: float
    max_expected_return: float


class ScenarioBacktester:
    """
    Lightweight scenario backtester.
    It perturbs expected edges to emulate market uncertainty.
    """

    def __init__(self, pipeline: ResearchPipeline) -> None:
        self.pipeline = pipeline

    def run(self, *, scenarios: int = 50, shock: float = 0.20, seed: int = 7) -> BacktestSummary:
        positions, _report = self.pipeline.run()
        if not positions:
            return BacktestSummary(
                scenarios=scenarios,
                avg_expected_return=0.0,
                min_expected_return=0.0,
                max_expected_return=0.0,
            )

        rng = Random(seed)
        scenario_returns: list[float] = []
        for _ in range(scenarios):
            value = 0.0
            for position in positions:
                perturbation = rng.uniform(-shock, shock)
                adjusted_edge = position.expected_edge * (1.0 + perturbation)
                value += position.weight * adjusted_edge
            scenario_returns.append(value)

        return BacktestSummary(
            scenarios=scenarios,
            avg_expected_return=mean(scenario_returns),
            min_expected_return=min(scenario_returns),
            max_expected_return=max(scenario_returns),
        )

