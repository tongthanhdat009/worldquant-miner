import json
from pathlib import Path

from polymarket_core.config import PipelineConfig
from polymarket_core.pipeline.e2e_pipeline import E2EPipeline


def test_e2e_pipeline_persists_artifact(tmp_path: Path) -> None:
    config = PipelineConfig(
        credentials_path=str(tmp_path / "missing_credentials.txt"),
        artifacts_dir=str(tmp_path / "artifacts"),
    )
    result = E2EPipeline(config=config).run()
    assert result.artifact_path.exists()
    payload = json.loads(result.artifact_path.read_text(encoding="utf-8"))
    assert payload["adapter"] == "PolymarketHTTPAdapter"
    assert "report" in payload
    assert payload["report"]["positions"] == len(payload["positions"])
    html_path = Path(payload["html_report"])
    assert html_path.exists()
    assert "<html" in html_path.read_text(encoding="utf-8").lower()

