from pathlib import Path

from polymarket_core.adapters.polymarket_http_adapter import PolymarketHTTPAdapter
from polymarket_core.config import PipelineConfig
from polymarket_core.pipeline.research_pipeline import ResearchPipeline


def test_pipeline_uses_http_without_credentials(tmp_path: Path) -> None:
    missing_file = tmp_path / "no_credentials.txt"
    pipeline = ResearchPipeline(config=PipelineConfig(credentials_path=str(missing_file)))
    assert isinstance(pipeline.adapter, PolymarketHTTPAdapter)


def test_pipeline_uses_http_adapter_with_credentials_file(tmp_path: Path) -> None:
    credentials_file = tmp_path / "credential.txt"
    credentials_file.write_text("POLYMARKET_API_KEY=test-key", encoding="utf-8")
    pipeline = ResearchPipeline(config=PipelineConfig(credentials_path=str(credentials_file)))
    assert isinstance(pipeline.adapter, PolymarketHTTPAdapter)


def test_pipeline_uses_http_adapter_with_clob_credentials_file(tmp_path: Path) -> None:
    credentials_file = tmp_path / "credential.txt"
    credentials_file.write_text(
        "\n".join(
            [
                "POLYMARKET_API_KEY=test-key",
                "POLYMARKET_API_SECRET=test-secret",
                "POLYMARKET_API_PASSPHRASE=test-passphrase",
            ]
        ),
        encoding="utf-8",
    )
    pipeline = ResearchPipeline(config=PipelineConfig(credentials_path=str(credentials_file)))
    assert isinstance(pipeline.adapter, PolymarketHTTPAdapter)

