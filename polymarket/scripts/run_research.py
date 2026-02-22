from polymarket_core.pipeline.research_pipeline import ResearchPipeline


def main() -> None:
    pipeline = ResearchPipeline()
    positions, report = pipeline.run()
    print("=== Polymarket Research Run ===")
    print(f"adapter={pipeline.adapter.__class__.__name__}")
    for position in positions:
        print(
            f"{position.market_id:28s} "
            f"weight={position.weight:.4f} edge={position.expected_edge:.4f}"
        )
    print("---")
    print(f"positions={report.positions}")
    print(f"gross_exposure={report.gross_exposure:.4f}")
    print(f"expected_return={report.expected_return:.4f}")


if __name__ == "__main__":
    main()

