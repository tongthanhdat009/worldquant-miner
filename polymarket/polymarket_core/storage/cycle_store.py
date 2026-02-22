from datetime import UTC, datetime
import json
from pathlib import Path
from uuid import uuid4

from polymarket_core.storage.html_report_renderer import HtmlReportRenderer


class CycleStore:
    def __init__(self, artifacts_dir: str) -> None:
        self.artifacts_dir = Path(artifacts_dir)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.renderer = HtmlReportRenderer()

    def save_cycle(self, payload: dict) -> Path:
        cycle_id = uuid4().hex
        data = {
            "cycle_id": cycle_id,
            "timestamp_utc": datetime.now(UTC).isoformat(),
            **payload,
        }
        path = self.artifacts_dir / f"cycle_{cycle_id}.json"
        html_path = self.artifacts_dir / f"cycle_{cycle_id}.html"
        data["html_report"] = str(html_path)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        html_content = self.renderer.render_cycle_report(data)
        self.renderer.write_html(html_content=html_content, output_path=html_path)
        return path

