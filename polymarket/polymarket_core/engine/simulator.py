from dataclasses import dataclass

from polymarket_core.portfolio.risk import PositionIntent


@dataclass(frozen=True)
class SimulationReport:
    expected_return: float
    gross_exposure: float
    positions: int


class PaperSimulator:
    """A simple expected-value style simulator for initial research loops."""

    def run(self, positions: list[PositionIntent]) -> SimulationReport:
        expected_return = sum(p.weight * p.expected_edge for p in positions)
        gross_exposure = sum(p.weight for p in positions)
        return SimulationReport(
            expected_return=expected_return,
            gross_exposure=gross_exposure,
            positions=len(positions),
        )

