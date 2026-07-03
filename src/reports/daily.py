from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Initiative:
    title: str
    objective: str
    kpi: str
    expected_business_impact: str
    confidence: float
    tasks: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "objective": self.objective,
            "kpi": self.kpi,
            "expected_business_impact": self.expected_business_impact,
            "confidence": self.confidence,
            "tasks": self.tasks,
        }


@dataclass(frozen=True)
class Recommendation:
    title: str
    reason: str
    estimated_impact: str
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "reason": self.reason,
            "estimated_impact": self.estimated_impact,
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class Task:
    title: str
    priority: str
    due_date: str
    estimated_impact: str
    confidence: float
    dependencies: list[str] = field(default_factory=list)
    reason: str = ""
    initiative: str = ""
    authority_policy: str = ""
    expected_outcome: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "priority": self.priority,
            "due_date": self.due_date,
            "estimated_impact": self.estimated_impact,
            "confidence": self.confidence,
            "dependencies": self.dependencies,
            "reason": self.reason,
            "initiative": self.initiative,
            "authority_policy": self.authority_policy,
            "expected_outcome": self.expected_outcome,
        }


@dataclass(frozen=True)
class DailyReport:
    company: str
    company_state: str
    date: str
    mission: str
    metrics: dict[str, Any]
    objective_status: dict[str, Any]
    decisions: list[str]
    initiatives: list[Initiative]
    recommendations: list[Recommendation]
    tasks: list[Task]
    chief_of_staff_plan: dict[str, Any]
    autonomous_action_log: list[dict[str, Any]]
    okr_status: dict[str, Any]
    board_advisors: list[dict[str, Any]]
    judgment_scorecard: dict[str, Any]
    prediction: dict[str, Any]
    prediction_evaluation: dict[str, Any]
    red_team_challenge: dict[str, Any]
    success_90_day_status: dict[str, Any]
    confidence: dict[str, float]
    risks: list[str]
    next_review: str
    knowledge_summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "company": self.company,
            "company_state": self.company_state,
            "date": self.date,
            "mission": self.mission,
            "metrics": self.metrics,
            "objective_status": self.objective_status,
            "decisions": self.decisions,
            "initiatives": [initiative.to_dict() for initiative in self.initiatives],
            "recommendations": [recommendation.to_dict() for recommendation in self.recommendations],
            "tasks": [task.to_dict() for task in self.tasks],
            "chief_of_staff_plan": self.chief_of_staff_plan,
            "autonomous_action_log": self.autonomous_action_log,
            "okr_status": self.okr_status,
            "board_advisors": self.board_advisors,
            "judgment_scorecard": self.judgment_scorecard,
            "prediction": self.prediction,
            "prediction_evaluation": self.prediction_evaluation,
            "red_team_challenge": self.red_team_challenge,
            "success_90_day_status": self.success_90_day_status,
            "confidence": self.confidence,
            "risks": self.risks,
            "next_review": self.next_review,
            "knowledge_summary": self.knowledge_summary,
        }
