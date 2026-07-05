from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from src.execution.connectors.base import ExecutionResult


class ExecutionLogWriter:
    """Append connector execution results to daily memory."""

    def __init__(self, memory_root: Path, timezone: str) -> None:
        self.memory_root = memory_root
        self.timezone = timezone
        self.executions_dir = memory_root / "executions"

    def append(self, run_date: str, results: list[ExecutionResult | dict[str, Any]]) -> Path:
        self.executions_dir.mkdir(parents=True, exist_ok=True)
        path = self.executions_dir / f"{run_date}.json"
        existing: list[dict[str, Any]] = []
        if path.exists():
            loaded = json.loads(path.read_text(encoding="utf-8") or "[]")
            if isinstance(loaded, list):
                existing = [item for item in loaded if isinstance(item, dict)]

        logged_at = datetime.now(ZoneInfo(self.timezone)).isoformat()
        normalized: list[dict[str, Any]] = []
        for result in results:
            payload = result.to_dict() if isinstance(result, ExecutionResult) else result
            if isinstance(payload, dict):
                normalized.append({**payload, "logged_at": payload.get("logged_at") or logged_at})

        path.write_text(
            json.dumps(existing + normalized, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return path
