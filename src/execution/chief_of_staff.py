from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.reports.daily import Task


@dataclass(frozen=True)
class ExecutionPlan:
    run_today: list[dict[str, Any]]
    can_wait: list[dict[str, Any]]
    conflicts: list[dict[str, Any]]
    autonomous_action_log: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_today": self.run_today,
            "can_wait": self.can_wait,
            "conflicts": self.conflicts,
            "autonomous_action_log": self.autonomous_action_log,
        }


class ChiefOfStaff:
    """Prioritizes executive work against delegated authority."""

    def __init__(self, delegated_authority: dict[str, Any]) -> None:
        self.delegated_authority = delegated_authority

    def plan(self, tasks: list[Task]) -> ExecutionPlan:
        ordered_tasks = sorted(tasks, key=self._task_sort_key)
        run_today: list[dict[str, Any]] = []
        can_wait: list[dict[str, Any]] = []
        conflicts: list[dict[str, Any]] = []
        action_log: list[dict[str, Any]] = []

        for task in ordered_tasks:
            policy_path, policy_value = self._authority_for_task(task)
            item = {
                "task": task.title,
                "initiative": task.initiative,
                "priority": task.priority,
                "expected_business_impact": task.estimated_impact,
                "confidence": task.confidence,
                "authority_policy": policy_path,
                "authority_value": policy_value,
            }

            if policy_value in {"always", True}:
                run_today.append(item)
                actual = "planned"
            elif policy_value == "draft_only":
                can_wait.append({**item, "reason": "Delegated authority allows preparation, not final send."})
                actual = "draft_only"
            elif policy_value in {"never", False, None}:
                conflicts.append({**item, "reason": "Decision exceeds delegated authority."})
                actual = "escalation_required"
            else:
                can_wait.append({**item, "reason": "No immediate execution slot selected by Chief of Staff."})
                actual = "waiting"

            action_log.append(
                {
                    "what_it_did": f"Classified task: {task.title}",
                    "why_it_did_it": task.reason,
                    "policy_authorized_it": f"{policy_path}={policy_value}",
                    "expected_outcome": task.expected_outcome or task.estimated_impact,
                    "actual_outcome": actual,
                }
            )

        return ExecutionPlan(
            run_today=run_today[:3],
            can_wait=can_wait + run_today[3:],
            conflicts=conflicts,
            autonomous_action_log=action_log,
        )

    def _task_sort_key(self, task: Task) -> tuple[int, float]:
        impact_rank = {"High": 0, "Medium": 1, "Low": 2}
        return (impact_rank.get(task.estimated_impact, 3), -task.confidence)

    def _authority_for_task(self, task: Task) -> tuple[str, Any]:
        title = task.title.lower()
        if "pricing" in title or "price" in title:
            return "business.change_pricing", self._get("business", "change_pricing")
        if "proposal" in title:
            return "sales.send_proposal", self._get("sales", "send_proposal")
        if "follow" in title:
            return "sales.follow_up", self._get("sales", "follow_up")
        if "demo" in title and "post" not in title:
            return "sales.schedule_demo", self._get("sales", "schedule_demo")
        if "campaign" in title and "pause" in title:
            return "ads.pause_campaigns", self._get("ads", "pause_campaigns")
        if "campaign" in title:
            return "ads.create_campaigns", self._get("ads", "create_campaigns")
        if "paid" in title or "spend" in title or "budget" in title or "promote" in title:
            return "ads.daily_budget_limit_ils", self._get("ads", "daily_budget_limit_ils")
        if "website" in title or "cta" in title:
            return "website.update_cta", self._get("website", "update_cta")
        if "image" in title:
            return "marketing.generate_images", self._get("marketing", "generate_images")
        if "video" in title or "script" in title:
            return "marketing.generate_video_scripts", self._get("marketing", "generate_video_scripts")
        if "post" in title or "content" in title or "reel" in title:
            return "marketing.publish_posts", self._get("marketing", "publish_posts")
        return "marketing.create_post_drafts", self._get("marketing", "create_post_drafts")

    def _get(self, section: str, key: str) -> Any:
        value = self.delegated_authority.get(section, {})
        if not isinstance(value, dict):
            return None
        return value.get(key)
