from __future__ import annotations

import json
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from src.decisions.engine import DecisionEngine
from src.providers.base import MetricSnapshot


class AutonomousOperatingPrincipleTests(unittest.TestCase):
    def test_empty_recommendations_create_growth_opportunity_scan_task(self) -> None:
        engine = DecisionEngine(
            company_config={
                "company": {"name": "ChatBot2U"},
                "marketing": {
                    "primary_kpi": "booked demos",
                    "budget_rule": {"amount_ils_per_day": 20},
                },
            },
            objectives_config={"company_state": "Validation", "targets": {"demos_per_week": 3}},
            company_knowledge="ChatBot2U sells WhatsApp automation.",
            timezone="Asia/Jerusalem",
        )

        tasks = engine._tasks_from_recommendations([], [], "2026-07-03")

        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].title, "Run autonomous growth opportunity scan")
        self.assertEqual(tasks[0].priority, "High")
        self.assertIn("never wait for work", tasks[0].reason)
        self.assertIn("SEO opportunities", tasks[0].reason)

    def test_decision_context_contains_never_wait_for_work_principle(self) -> None:
        snapshot = MetricSnapshot(
            provider="mock",
            collected_at=datetime(2026, 7, 3, 8, 0, tzinfo=ZoneInfo("Asia/Jerusalem")),
            metrics={
                "booked_demos": 1,
                "target_booked_demos": 3,
                "qualified_leads": 2,
                "whatsapp_clicks": 10,
                "estimated_spend_ils": 0,
            },
        )
        context = DecisionEngine(
            company_config={
                "company": {"name": "ChatBot2U"},
                "marketing": {
                    "primary_kpi": "booked demos",
                    "budget_rule": {"amount_ils_per_day": 20},
                },
            },
            objectives_config={"company_state": "Validation", "targets": {"demos_per_week": 3}},
            company_knowledge="ChatBot2U sells WhatsApp automation.",
            timezone="Asia/Jerusalem",
        ).evaluate([snapshot])

        payload = json.dumps(context.to_prompt_payload(), ensure_ascii=False)

        self.assertIn("Never wait for work", payload)
        self.assertIn("competitors", payload)
        self.assertIn("WhatsApp conversations", payload)

    def test_decision_context_contains_delegated_authority_and_chief_of_staff_plan(self) -> None:
        snapshot = MetricSnapshot(
            provider="mock",
            collected_at=datetime(2026, 7, 3, 8, 0, tzinfo=ZoneInfo("Asia/Jerusalem")),
            metrics={
                "booked_demos": 1,
                "target_booked_demos": 3,
                "qualified_leads": 2,
                "whatsapp_clicks": 10,
                "estimated_spend_ils": 0,
            },
        )
        context = DecisionEngine(
            company_config={
                "company": {"name": "ChatBot2U"},
                "marketing": {
                    "primary_kpi": "booked demos",
                    "budget_rule": {"amount_ils_per_day": 20},
                },
            },
            objectives_config={
                "company_state": "Validation",
                "targets": {"demos_per_week": 3},
                "quarterly_okrs": {
                    "objective": "Become the leading AI automation platform for Israeli law firms.",
                    "key_results": {
                        "paying_customers": 15,
                        "demos": 60,
                        "qualified_leads": 500,
                    },
                },
                "delegated_authority": {
                    "marketing": {"publish_posts": "always", "create_post_drafts": "always"},
                    "ads": {"create_campaigns": "always", "daily_budget_limit_ils": 20},
                    "sales": {"schedule_demo": "always", "send_proposal": "draft_only"},
                    "business": {"change_pricing": "never"},
                },
            },
            company_knowledge="ChatBot2U sells WhatsApp automation.",
            timezone="Asia/Jerusalem",
        ).evaluate([snapshot])

        payload = context.to_prompt_payload()
        delegated_authority = payload["summary"]["delegated_authority"]
        report = payload["daily_report"]
        decision_text = json.dumps(payload["decisions"], ensure_ascii=False)

        self.assertEqual(delegated_authority["marketing"]["publish_posts"], "always")
        self.assertEqual(delegated_authority["business"]["change_pricing"], "never")
        self.assertIn("delegated authority", decision_text)
        self.assertIn("run_today", report["chief_of_staff_plan"])
        self.assertIn("conflicts", report["chief_of_staff_plan"])
        self.assertGreater(len(report["initiatives"]), 0)
        self.assertGreater(len(report["autonomous_action_log"]), 0)
        self.assertEqual(report["okr_status"]["key_results"]["demos"]["target"], 60)
        self.assertEqual(len(report["board_advisors"]), 5)
        self.assertIn("Growth Advisor", json.dumps(report["board_advisors"], ensure_ascii=False))
        self.assertIn("Design System Advisor", json.dumps(report["board_advisors"], ensure_ascii=False))

    def test_decision_context_contains_operator_execution_queue(self) -> None:
        snapshot = MetricSnapshot(
            provider="whatsapp_bot",
            collected_at=datetime(2026, 7, 5, 8, 0, tzinfo=ZoneInfo("Asia/Jerusalem")),
            metrics={
                "whatsapp_bot": {
                    "available": False,
                    "verified": False,
                    "reason": "No verified WhatsApp event data available.",
                },
                "meta_ads": {
                    "available": False,
                    "verified": False,
                    "campaign_status": "unknown",
                    "campaign_status_note": "No campaign has been verified as active.",
                },
                "marketing_platform": {
                    "mcp": {"requires_external_mcp_execution": True},
                    "metrics_available": False,
                },
            },
        )
        context = DecisionEngine(
            company_config={
                "company": {"name": "ChatBot2U"},
                "marketing": {
                    "primary_kpi": "booked demos",
                    "budget_rule": {"amount_ils_per_day": 20},
                },
            },
            objectives_config={
                "company_state": "Validation",
                "targets": {"demos_per_week": 3},
                "delegated_authority": {
                    "marketing": {
                        "publish_posts": "always",
                        "create_post_drafts": "always",
                        "publish_reels": "always",
                    },
                    "website": {"update_cta": "always"},
                    "ads": {"create_campaigns": "always", "daily_budget_limit_ils": 20},
                    "sales": {"schedule_demo": "always", "follow_up": "always"},
                },
            },
            company_knowledge="ChatBot2U sells WhatsApp automation.",
            timezone="Asia/Jerusalem",
        ).evaluate([snapshot])

        summary = context.summary
        queue = summary["execution_queue"]

        self.assertEqual(queue["initiative"], "Acquire the first three paying law firms")
        self.assertEqual(queue["today_mission"], "Generate one additional paying customer.")
        self.assertIn("currently_working_on", queue)
        self.assertIn("internal_tasks", queue)
        self.assertIn(
            "Generate one additional paying customer",
            summary["recommended_actions"],
        )
        self.assertTrue(
            any(task["task"] == "Reconnect Meta MCP / Graph metric sync" for task in queue["internal_tasks"])
        )
        self.assertTrue(
            any(task["ceo_visible"] is False for task in queue["internal_tasks"])
        )


if __name__ == "__main__":
    unittest.main()
