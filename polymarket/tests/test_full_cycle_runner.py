import json
from pathlib import Path

from polymarket_core.config import PipelineConfig
from polymarket_core.cycle.full_cycle_runner import FullCycleRunner


def test_full_cycle_rejects_and_skips_execution(tmp_path: Path) -> None:
    config = PipelineConfig(
        credentials_path=str(tmp_path / "missing_credentials.txt"),
        artifacts_dir=str(tmp_path / "artifacts"),
        cycle_min_avg_return=0.9,
    )
    result = FullCycleRunner(config).run(mode="paper", auto_execute=True)
    assert not result.approved
    assert not result.executed
    assert result.e2e_artifact is None
    cycle_path = Path(result.cycle_artifact)
    assert cycle_path.exists()
    payload = json.loads(cycle_path.read_text(encoding="utf-8"))
    assert Path(payload["html_report"]).exists()


def test_full_cycle_approves_and_executes_paper(tmp_path: Path) -> None:
    config = PipelineConfig(
        credentials_path=str(tmp_path / "missing_credentials.txt"),
        artifacts_dir=str(tmp_path / "artifacts"),
        cycle_min_avg_return=-1.0,
        cycle_min_worst_return=-1.0,
    )
    result = FullCycleRunner(config).run(mode="paper", auto_execute=True)
    assert result.approved
    assert result.executed
    assert result.e2e_artifact is not None
    payload = json.loads(Path(result.cycle_artifact).read_text(encoding="utf-8"))
    assert payload["approved"] is True
    assert payload["executed"] is True
    assert Path(payload["html_report"]).exists()
    run_payload = json.loads(Path(result.e2e_artifact).read_text(encoding="utf-8"))
    assert Path(run_payload["html_report"]).exists()

