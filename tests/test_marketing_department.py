from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from src.channels.file_output import FileOutputChannel
from src.decisions.engine import DecisionEngine
from src.execution.marketing_department import (
    MarketingDepartment,
    attach_marketing_department_output,
)
from src.providers.base import MetricSnapshot


def _company_config() -> dict:
    return {
        "company": {"name": "ChatBot2U", "recipient_email": "rami@gateco.ai"},
        "marketing": {
            "primary_kpi": "booked demos",
            "cta": {"channel": "WhatsApp", "phone": "+972559720244"},
            "budget_rule": {
                "amount_ils_per_day": 20,
                "saturday": "no spend",
                "friday": "morning only",
                "note": "Keep spend focused on qualified demo bookings.",
            },
        },
    }


def _objectives_config() -> dict:
    return {
        "company_state": "Validation",
        "targets": {"demos_per_week": 3},
        "delegated_authority": {
            "marketing": {
                "create_posts": "always",
                "publish_posts": "always",
                "create_post_drafts": "always",
                "generate_images": "always",
                "generate_video_scripts": "always",
                "publish_reels": "always",
            },
            "ads": {
                "create_campaigns": "always",
                "pause_campaigns": "always",
                "daily_budget_limit_ils": 20,
            },
            "website": {"update_cta": "always", "update_copy": "always"},
            "sales": {"follow_up": "always", "send_proposal": "draft_only"},
        },
    }


def _context():
    snapshot = MetricSnapshot(
        provider="production_unavailable",
        collected_at=datetime(2026, 7, 5, 8, 0, tzinfo=ZoneInfo("Asia/Jerusalem")),
        metrics={
            "whatsapp_bot": {
                "available": False,
                "verified": False,
                "source": "unavailable",
                "today": {},
            },
            "meta_ads": {
                "available": False,
                "verified": False,
                "source": "unavailable",
                "campaign_status": "unknown",
                "campaign_status_note": "No campaign has been verified as active.",
            },
            "marketing_platform": {"metrics_available": False},
            "website_intelligence": {
                "missing_or_weak_ctas": ["Hero CTA does not clearly ask for a demo."]
            },
        },
    )
    return DecisionEngine(
        company_config=_company_config(),
        objectives_config=_objectives_config(),
        company_knowledge="ChatBot2U sells WhatsApp automation.",
        timezone="Asia/Jerusalem",
    ).evaluate([snapshot])


class MarketingDepartmentTests(unittest.TestCase):
    def test_marketing_department_has_eight_agents_and_truthful_blockers(self) -> None:
        output = MarketingDepartment(
            company_config=_company_config(),
            objectives_config=_objectives_config(),
            timezone="Asia/Jerusalem",
        ).run(_context())

        payload = output.to_dict()
        agents = [agent["name"] for agent in payload["agents"]]
        actions = {action["agent"]: action for action in payload["action_log"]}

        self.assertEqual(len(agents), 8)
        self.assertEqual(agents[0], "Content Agent")
        self.assertIn("Outreach Agent", agents)
        self.assertEqual(actions["Content Agent"]["status"], "prepared")
        self.assertEqual(actions["Social Agent"]["status"], "blocked")
        self.assertEqual(actions["Ads Agent"]["status"], "blocked")
        self.assertFalse(actions["Social Agent"]["result"]["executed"])
        self.assertFalse(actions["Ads Agent"]["result"]["executed"])
        self.assertEqual(actions["Social Agent"]["result"]["recorded_post_ids"], [])

    def test_marketing_department_attaches_to_decision_context(self) -> None:
        context = _context()
        output = MarketingDepartment(
            company_config=_company_config(),
            objectives_config=_objectives_config(),
            timezone="Asia/Jerusalem",
        ).run(context)

        attach_marketing_department_output(context, output)

        self.assertIn("marketing_department", context.summary)
        self.assertEqual(
            context.summary["execution_departments"]["active_department"],
            "Marketing Operations",
        )
        self.assertIn("Prepared today's law-firm Reel content plan", context.summary["prepared_actions"])
        self.assertIn("Checked social publishing readiness", context.summary["blocked_actions"])

    def test_file_output_writes_daily_action_memory(self) -> None:
        context = _context()
        output = MarketingDepartment(
            company_config=_company_config(),
            objectives_config=_objectives_config(),
            timezone="Asia/Jerusalem",
        ).run(context)
        attach_marketing_department_output(context, output)

        with tempfile.TemporaryDirectory() as tmpdir:
            result = FileOutputChannel(Path(tmpdir), "Asia/Jerusalem").deliver(
                decision_context=context,
                brief="Daily brief",
                sent=False,
                dry_run=False,
            )
            actions_path = result.paths["actions"]
            actions = json.loads(actions_path.read_text(encoding="utf-8"))

        self.assertTrue(actions_path.name.endswith(".json"))
        self.assertEqual(len(actions), 8)
        self.assertEqual(actions[0]["initiative"], "Acquire the first three paying law firms")
        self.assertIn("delegated_authority_used", actions[0])


if __name__ == "__main__":
    unittest.main()
