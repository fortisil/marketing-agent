from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from src.channels.base import OutputResult
from src.decisions.engine import DecisionContext
from src.execution.action_log import ActionLogWriter
from src.execution.connectors.log import ExecutionLogWriter


class FileOutputChannel:
    name = "file"

    def __init__(self, root: Path, timezone: str) -> None:
        self.root = root
        self.timezone = timezone
        self.briefs_dir = root / "briefs"
        self.reports_dir = root / "reports"
        self.decisions_dir = root / "decisions"
        self.runs_dir = root / "runs"

    def deliver(
        self,
        decision_context: DecisionContext,
        brief: str,
        sent: bool,
        dry_run: bool,
        delivery: dict[str, Any] | None = None,
    ) -> OutputResult:
        self._ensure()
        run_id = datetime.now(ZoneInfo(self.timezone)).strftime("%Y%m%d-%H%M%S")
        run_date = decision_context.run_date

        brief_path = self.briefs_dir / f"{run_date}.md"
        report_path = self.reports_dir / f"{run_date}.json"
        decision_path = self.decisions_dir / f"{run_date}.json"
        run_path = self.runs_dir / f"{run_id}.json"
        actions_path = self.root / "actions" / f"{run_date}.json"
        executions_path = self.root / "executions" / f"{run_date}.json"

        brief_path.write_text(brief + "\n", encoding="utf-8")
        report = decision_context.daily_report.to_dict()
        if delivery:
            report["delivery"] = delivery
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        department_actions = (
            report.get("metrics", {})
            .get("marketing_department", {})
            .get("action_log", [])
        )
        if isinstance(department_actions, list) and department_actions:
            actions_path = ActionLogWriter(self.root, self.timezone).append(run_date, department_actions)
        execution_results = (
            report.get("metrics", {})
            .get("marketing_department", {})
            .get("execution_results", [])
        )
        if isinstance(execution_results, list) and execution_results:
            executions_path = ExecutionLogWriter(self.root, self.timezone).append(
                run_date,
                execution_results,
            )
        decision_path.write_text(
            json.dumps(decision_context.to_prompt_payload(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        run_record: dict[str, Any] = {
            "run_id": run_id,
            "run_date": run_date,
            "created_at": datetime.now(ZoneInfo(self.timezone)).isoformat(),
            "sent": sent,
            "dry_run": dry_run,
            "brief_path": str(brief_path),
            "report_path": str(report_path),
            "decision_path": str(decision_path),
            "channel": self.name,
        }
        if delivery:
            run_record["delivery"] = delivery
        run_path.write_text(json.dumps(run_record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        return OutputResult(
            channel=self.name,
            paths={
                "brief": brief_path,
                "report": report_path,
                "decision": decision_path,
                "run": run_path,
                "actions": actions_path,
                "executions": executions_path,
            },
            message=f"Saved brief to {brief_path}",
        )

    def _ensure(self) -> None:
        self.briefs_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.decisions_dir.mkdir(parents=True, exist_ok=True)
        self.runs_dir.mkdir(parents=True, exist_ok=True)
