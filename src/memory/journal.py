from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


def write_evening_journal(memory_path: Path, timezone: str) -> dict[str, Path]:
    reports_dir = memory_path / "reports"
    journals_dir = memory_path / "journals"
    journals_dir.mkdir(parents=True, exist_ok=True)

    report_path = _latest_report_path(reports_dir)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    run_date = str(report.get("date") or datetime.now(ZoneInfo(timezone)).date().isoformat())
    journal = _journal_from_report(report, timezone)

    markdown_path = journals_dir / f"{run_date}.md"
    json_path = journals_dir / f"{run_date}.json"
    markdown_path.write_text(_journal_markdown(journal) + "\n", encoding="utf-8")
    json_path.write_text(json.dumps(journal, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"journal": markdown_path, "journal_json": json_path, "source_report": report_path}


def _latest_report_path(reports_dir: Path) -> Path:
    candidates = sorted(reports_dir.glob("*.json"))
    if not candidates:
        raise FileNotFoundError("No daily reports found. Generate a brief before writing the evening journal.")
    return candidates[-1]


def _journal_from_report(report: dict[str, Any], timezone: str) -> dict[str, Any]:
    recommendations = report.get("recommendations", [])
    risks = report.get("risks", [])
    okr_status = report.get("okr_status", {})
    action_log = report.get("autonomous_action_log", [])
    return {
        "date": report.get("date"),
        "created_at": datetime.now(ZoneInfo(timezone)).isoformat(),
        "questions": {
            "what_did_i_learn_today": _learning_from_report(report),
            "which_recommendation_was_wrong": "Unknown until outcomes are measured; review tomorrow against actual funnel data.",
            "what_surprised_me": risks[0] if risks else "No major surprise recorded in today's data.",
            "what_should_i_change_tomorrow": _tomorrow_change(recommendations, okr_status),
        },
        "autonomous_action_review": action_log,
        "learning": {
            "prediction": recommendations[0] if recommendations else {},
            "reality": "Pending next metrics sync.",
            "improvement": "Compare tomorrow's WhatsApp, demo, customer, and campaign metrics against today's expected outcomes.",
        },
    }


def _learning_from_report(report: dict[str, Any]) -> str:
    funnel = report.get("metrics", {}).get("whatsapp_bot", {})
    bottleneck = funnel.get("today_bottleneck") or funnel.get("today", {}).get("bottleneck")
    if bottleneck:
        return f"Today's clearest learning is the funnel bottleneck: {bottleneck}."
    return "The AI CMO needs more outcome data to produce stronger learning."


def _tomorrow_change(recommendations: list[dict[str, Any]], okr_status: dict[str, Any]) -> str:
    if recommendations:
        return f"Start by validating whether this recommendation moved the business: {recommendations[0].get('title')}."
    daily_question = okr_status.get("daily_question", "What action most helps acquire another paying customer?")
    return f"Ask again tomorrow: {daily_question}"


def _journal_markdown(journal: dict[str, Any]) -> str:
    questions = journal["questions"]
    return "\n".join(
        [
            f"# Executive Journal - {journal.get('date')}",
            "",
            "## What did I learn today?",
            questions["what_did_i_learn_today"],
            "",
            "## Which recommendation was wrong?",
            questions["which_recommendation_was_wrong"],
            "",
            "## What surprised me?",
            questions["what_surprised_me"],
            "",
            "## What should I change tomorrow?",
            questions["what_should_i_change_tomorrow"],
        ]
    )
