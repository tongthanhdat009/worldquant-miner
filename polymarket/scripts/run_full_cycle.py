import argparse
import json
from pathlib import Path

from polymarket_core.config import PipelineConfig
from polymarket_core.cycle.full_cycle_runner import FullCycleRunner


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run full cycle research->backtest->execute.")
    parser.add_argument("--mode", choices=["paper", "live"], default="paper")
    parser.add_argument("--confirm-live", action="store_true")
    parser.add_argument("--auto-execute", action="store_true", default=False)
    parser.add_argument("--scenarios", type=int, default=80)
    parser.add_argument("--shock", type=float, default=0.25)
    parser.add_argument("--min-avg-return", type=float, default=0.02)
    parser.add_argument("--min-worst-return", type=float, default=-0.05)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    config = PipelineConfig(
        execution_mode=args.mode,
        cycle_backtest_scenarios=args.scenarios,
        cycle_backtest_shock=args.shock,
        cycle_min_avg_return=args.min_avg_return,
        cycle_min_worst_return=args.min_worst_return,
    )
    result = FullCycleRunner(config).run(
        mode=args.mode,
        confirm_live=args.confirm_live,
        auto_execute=args.auto_execute,
    )
    cycle_payload = json.loads(Path(result.cycle_artifact).read_text(encoding="utf-8"))
    print(
        json.dumps(
            {
                "approved": result.approved,
                "decision_reason": result.decision_reason,
                "research_expected_return": result.research_expected_return,
                "backtest": {
                    "scenarios": result.backtest.scenarios,
                    "avg_expected_return": result.backtest.avg_expected_return,
                    "min_expected_return": result.backtest.min_expected_return,
                    "max_expected_return": result.backtest.max_expected_return,
                },
                "executed": result.executed,
                "e2e_artifact": result.e2e_artifact,
                "cycle_artifact": result.cycle_artifact,
                "cycle_html_report": cycle_payload.get("html_report", ""),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

