import argparse
import json
from pathlib import Path

from polymarket_core.config import PipelineConfig
from polymarket_core.pipeline.e2e_pipeline import E2EPipeline


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Polymarket end-to-end pipeline.")
    parser.add_argument(
        "--mode",
        choices=["paper", "live"],
        default="paper",
        help="Execution mode. 'live' places real orders.",
    )
    parser.add_argument(
        "--confirm-live",
        action="store_true",
        help="Required safety flag for --mode live.",
    )
    parser.add_argument(
        "--max-orders",
        type=int,
        default=3,
        help="Maximum number of orders to send in live mode.",
    )
    parser.add_argument(
        "--min-edge",
        type=float,
        default=0.06,
        help="Minimum edge threshold for live order submission.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    config = PipelineConfig(
        execution_mode=args.mode,
        live_max_orders=args.max_orders,
        live_min_edge=args.min_edge,
    )
    result = E2EPipeline(config=config, confirm_live=args.confirm_live).run()
    payload = json.loads(Path(result.artifact_path).read_text(encoding="utf-8"))
    print("=== Polymarket E2E Run ===")
    print(f"mode={args.mode}")
    print(f"adapter={result.adapter}")
    print(f"positions={len(result.positions)}")
    print(f"orders={len(result.orders)}")
    print(f"gross_exposure={result.report.gross_exposure:.4f}")
    print(f"expected_return={result.report.expected_return:.4f}")
    print(f"artifact={result.artifact_path}")
    print(f"html_report={payload.get('html_report', '')}")


if __name__ == "__main__":
    main()

