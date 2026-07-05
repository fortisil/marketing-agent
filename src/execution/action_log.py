from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


class ActionLogWriter:
    """Append department action records to daily memory."""

    def __init__(self, memory_root: Path, timezone: str) -> None:
        self.memory_root = memory_root
        self.timezone = timezone
        self.actions_dir = memory_root / "actions"

    def append(self, run_date: str, actions: list[dict[str, Any]]) -> Path:
        self.actions_dir.mkdir(parents=True, exist_ok=True)
        path = self.actions_dir / f"{run_date}.json"
        existing: list[dict[str, Any]] = []
        if path.exists():
            loaded = json.loads(path.read_text(encoding="utf-8") or "[]")
            if isinstance(loaded, list):
                existing = [item for item in loaded if isinstance(item, dict)]

        timestamp = datetime.now(ZoneInfo(self.timezone)).isoformat()
        normalized = [
            {**action, "logged_at": action.get("logged_at") or timestamp}
            for action in actions
            if isinstance(action, dict)
        ]
        path.write_text(
            json.dumps(existing + normalized, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return path
