from __future__ import annotations

from pathlib import Path

from src.decisions.engine import DecisionContext
from src.channels.file_output import FileOutputChannel


class MemoryStore:
    def __init__(self, root: Path, timezone: str) -> None:
        self.root = root
        self.timezone = timezone
        self.briefs_dir = root / "briefs"
        self.decisions_dir = root / "decisions"
        self.reports_dir = root / "reports"
        self.runs_dir = root / "runs"

    def ensure(self) -> None:
        self.briefs_dir.mkdir(parents=True, exist_ok=True)
        self.decisions_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.runs_dir.mkdir(parents=True, exist_ok=True)

    def save_daily_memory(
        self,
        decision_context: DecisionContext,
        brief: str,
        sent: bool,
        dry_run: bool,
    ) -> dict[str, Path]:
        result = FileOutputChannel(self.root, self.timezone).deliver(
            decision_context=decision_context,
            brief=brief,
            sent=sent,
            dry_run=dry_run,
        )
        return result.paths
