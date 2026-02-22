from polymarket_core.config import PipelineConfig
from polymarket_core.pipeline.research_pipeline import ResearchPipeline


def test_pipeline_smoke() -> None:
    pipeline = ResearchPipeline(config=PipelineConfig(credentials_path="missing.txt"))
    positions, report = pipeline.run()
    assert report.positions == len(positions)
    assert report.gross_exposure >= 0

