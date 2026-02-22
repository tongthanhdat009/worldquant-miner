from dataclasses import asdict
from datetime import datetime, UTC
import json
from pathlib import Path
from uuid import uuid4

from polymarket_core.engine.simulator import SimulationReport
from polymarket_core.execution.types import ExecutedOrder
from polymarket_core.portfolio.risk import PositionIntent
from polymarket_core.storage.html_report_renderer import HtmlReportRenderer


class RunStore:
    def __init__(self, artifacts_dir: str) -> None:
        self.artifacts_dir = Path(artifacts_dir)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.renderer = HtmlReportRenderer()

    def save_run(
        self,
        *,
        adapter_name: str,
        positions: list[PositionIntent],
        orders: list[ExecutedOrder],
        report: SimulationReport,
    ) -> Path:
        run_id = uuid4().hex
        timestamp = datetime.now(UTC).isoformat()
        payload = {
            "run_id": run_id,
            "timestamp_utc": timestamp,
            "adapter": adapter_name,
            "positions": [asdict(item) for item in positions],
            "orders": [asdict(item) for item in orders],
            "report": asdict(report),
        }
        file_path = self.artifacts_dir / f"run_{run_id}.json"
        html_path = self.artifacts_dir / f"run_{run_id}.html"
        payload["html_report"] = str(html_path)
        file_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        html_content = self.renderer.render_run_report(payload)
        self.renderer.write_html(html_content=html_content, output_path=html_path)
        return file_path

