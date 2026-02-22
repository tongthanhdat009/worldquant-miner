import pytest

from polymarket_core.config import PipelineConfig
from polymarket_core.pipeline.e2e_pipeline import E2EPipeline


def test_live_mode_requires_confirmation(tmp_path) -> None:
    config = PipelineConfig(
        execution_mode="live",
        credentials_path=str(tmp_path / "missing_credentials.txt"),
    )
    with pytest.raises(RuntimeError, match="not confirmed"):
        E2EPipeline(config=config, confirm_live=False)


def test_live_mode_requires_credentials(tmp_path) -> None:
    config = PipelineConfig(
        execution_mode="live",
        credentials_path=str(tmp_path / "missing_credentials.txt"),
    )
    with pytest.raises(RuntimeError, match="requires credentials"):
        E2EPipeline(config=config, confirm_live=True)

