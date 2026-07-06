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
        "company": {
            "name": "ChatBot2U",
            "recipient_email": "rami@gateco.ai",
            "internal_language": "English",
        },
        "marketing": {
            "primary_kpi": "booked demos",
            "marketing_language": "Hebrew",
            "default_post_language": "Hebrew",
            "target_country": "Israel",
            "target_audience": ["Israeli law firms"],
            "cta": {
                "channel": "WhatsApp",
                "phone": "+972559720244",
                "link": "https://wa.me/972559720244",
                "required_in_posts": True,
                "default_hebrew": (
                    "רוצים לראות איך זה עובד? שלחו הודעה ל-WhatsApp: "
                    "https://wa.me/972559720244"
                ),
            },
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
        with tempfile.TemporaryDirectory() as tmpdir:
            output = MarketingDepartment(
                company_config=_company_config(),
                objectives_config=_objectives_config(),
                timezone="Asia/Jerusalem",
                memory_root=Path(tmpdir),
            ).run(_context())

        payload = output.to_dict()
        agents = [agent["name"] for agent in payload["agents"]]
        actions = {action["agent"]: action for action in payload["action_log"]}

        self.assertEqual(len(agents), 8)
        self.assertEqual(agents[0], "Content Agent")
        self.assertIn("Outreach Agent", agents)
        self.assertEqual(actions["Content Agent"]["status"], "internal_memory")
        self.assertEqual(actions["Content Agent"]["result"]["language"], "Hebrew")
        self.assertEqual(actions["Content Agent"]["result"]["internal_language"], "English")
        self.assertEqual(actions["Content Agent"]["result"]["whatsapp_link"], "https://wa.me/972559720244")
        self.assertIn("שלחו הודעה ל-WhatsApp", actions["Content Agent"]["result"]["cta"])
        self.assertNotIn("Book a demo", actions["Content Agent"]["result"]["cta"])
        self.assertEqual(actions["Design Agent"]["result"]["image_provider"], "openai")
        self.assertEqual(actions["Design Agent"]["result"]["text_policy"], "no_model_rendered_text")
        self.assertIn("No text, no letters", actions["Design Agent"]["result"]["image_prompt"])
        self.assertNotIn("clear Hebrew WhatsApp demo CTA", actions["Design Agent"]["result"]["image_prompt"])
        self.assertEqual(actions["Design Agent"]["status"], "blocked")
        self.assertEqual(actions["Social Agent"]["status"], "blocked")
        self.assertEqual(actions["Ads Agent"]["status"], "blocked")
        self.assertFalse(actions["Social Agent"]["result"]["executed"])
        self.assertFalse(actions["Ads Agent"]["result"]["executed"])
        self.assertEqual(actions["Social Agent"]["result"]["recorded_post_ids"], [])
        self.assertEqual(payload["execution_results"][0]["connector"], "ImageExecutor")
        self.assertEqual(payload["execution_results"][0]["status"], "blocked")
        self.assertEqual(len(payload["workforce"]["tasks"]), 1)
        self.assertEqual(payload["workforce"]["tasks"][0]["status"], "Blocked")

    def test_social_caption_is_hebrew_first_with_mandatory_whatsapp_cta(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = MarketingDepartment(
                company_config=_company_config(),
                objectives_config=_objectives_config(),
                timezone="Asia/Jerusalem",
                memory_root=Path(tmpdir),
            ).run(_context())

        content = {
            item.agent: item.daily_output
            for item in output.outputs
        }["Content Agent"]

        self.assertEqual(content["language"], "Hebrew")
        self.assertEqual(content["marketing_language"], "Hebrew")
        self.assertEqual(content["target_country"], "Israel")
        self.assertEqual(content["target_audience"], ["Israeli law firms"])
        self.assertTrue(content["cta_required"])
        self.assertIn("עורכי דין", content["hebrew_copy"])
        self.assertIn("https://wa.me/972559720244", content["cta"])
        self.assertNotIn("Book a demo", content["cta"])

    def test_aeos_spec_outputs_are_business_outcome_oriented(self) -> None:
        context = _context()
        with tempfile.TemporaryDirectory() as tmpdir:
            output = MarketingDepartment(
                company_config=_company_config(),
                objectives_config=_objectives_config(),
                timezone="Asia/Jerusalem",
                memory_root=Path(tmpdir),
            ).run(context)

        payload = output.to_dict()

        self.assertEqual(
            payload["aeos_spec"]["primary_objective"],
            "Acquire additional paying customers.",
        )
        self.assertEqual(payload["aeos_spec"]["north_star_priority_order"][0], "Paying Customers")
        self.assertIn("Creative Director", payload["organization"]["workers"])
        self.assertIn("Promotion Manager", payload["organization"]["workers"])
        self.assertIn("Analytics Manager", payload["organization"]["workers"])
        creative_brief = payload["creative_brief"]
        for key in [
            "campaign_objective",
            "target_audience",
            "pain",
            "promise",
            "offer",
            "proof",
            "headline",
            "supporting_copy",
            "cta",
            "landing_page",
            "promotion_strategy",
            "success_metric",
        ]:
            self.assertIn(key, creative_brief)
        self.assertEqual(creative_brief["marketing_language"], "Hebrew")
        self.assertEqual(creative_brief["internal_operating_language"], "English")
        self.assertIn("https://wa.me/972559720244", creative_brief["landing_page"])
        self.assertEqual(payload["budget_status"]["daily_budget_limit_ils"], 20)
        self.assertEqual(payload["budget_status"]["monthly_budget_limit_ils"], 600)
        self.assertTrue(payload["budget_status"]["one_active_promotion_per_asset"])
        self.assertEqual(payload["content_intelligence"]["status"], "unavailable")
        self.assertIsNone(payload["content_intelligence"]["business_value_score"])
        self.assertIn("stop_continue_improve_scale", payload["growth_intelligence"])
        self.assertEqual(payload["promotion_brain"]["decision"], "pause")
        self.assertEqual(payload["promotion_brain"]["status"], "blocked")
        self.assertIn("spend_reconciliation", payload["budget_guard"]["failed_rules"])
        self.assertFalse(payload["budget_guard"]["campaign_creation_allowed"])
        self.assertEqual(payload["video_production"]["requirements"]["language"], "Hebrew")
        self.assertEqual(payload["video_production"]["requirements"]["aspect_ratio"], "9:16")
        self.assertFalse(payload["video_production"]["requirements"]["subtitles"])
        self.assertIn("Logos", payload["brand_brain"]["maintains"])
        self.assertIn("OpenAI", payload["connector_health"])
        self.assertIn("HeyGen", payload["connector_health"])
        self.assertIn("Google Analytics 4", payload["connector_health"])
        self.assertIn("blocking_issues", payload["monitoring"])
        self.assertEqual(payload["weekly_executive_review"]["schedule"], "Every Sunday")
        self.assertTrue(payload["acceptance_criteria"]["budget_enforcement"])
        self.assertFalse(payload["acceptance_criteria"]["system_complete"])
        self.assertFalse(payload["final_definition_of_done"]["complete"])
        self.assertEqual(payload["hypothesis_register"][0]["result"], "pending_verified_attribution")
        self.assertEqual(payload["decision_ledger"][0]["learning"], "pending_verified_outcomes")

        attach_marketing_department_output(context, output)
        self.assertIn("creative_brief", context.summary)
        self.assertIn("budget_status", context.summary)
        self.assertIn("content_intelligence", context.summary)
        self.assertIn("growth_intelligence", context.summary)
        self.assertIn("promotion_brain", context.summary)
        self.assertIn("budget_guard", context.summary)
        self.assertIn("connector_health", context.summary)
        self.assertIn("monitoring", context.summary)
        self.assertIn("weekly_executive_review", context.summary)
        self.assertIn("acceptance_criteria", context.summary)
        self.assertIn("final_definition_of_done", context.summary)
        self.assertIn("decision_ledger", context.summary)
        self.assertIn("business_memory", context.summary)
        self.assertIn("30 consecutive days", context.summary["execution_departments"]["success_criterion"])

    def test_video_specs_use_heygen_without_subtitles_for_instagram_reels(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = MarketingDepartment(
                company_config=_company_config(),
                objectives_config=_objectives_config(),
                timezone="Asia/Jerusalem",
                memory_root=Path(tmpdir),
            ).run(_context())

        video = {
            item.agent: item.daily_output
            for item in output.outputs
        }["Video Agent"]

        self.assertEqual(video["language"], "Hebrew")
        self.assertEqual(video["renderer"], "HeyGen")
        self.assertEqual(video["format"], "Instagram Reels")
        self.assertEqual(video["aspect_ratio"], "9:16")
        self.assertEqual(video["resolution"], "1080x1920")
        self.assertFalse(video["subtitles"])
        self.assertEqual(video["captions"], "none")
        self.assertIn("שלחו הודעה ל-WhatsApp", video["heygen_script"])

    def test_marketing_department_attaches_to_decision_context(self) -> None:
        context = _context()
        with tempfile.TemporaryDirectory() as tmpdir:
            output = MarketingDepartment(
                company_config=_company_config(),
                objectives_config=_objectives_config(),
                timezone="Asia/Jerusalem",
                memory_root=Path(tmpdir),
            ).run(context)

        attach_marketing_department_output(context, output)

        self.assertIn("marketing_department", context.summary)
        self.assertEqual(
            context.summary["execution_departments"]["active_department"],
            "Marketing Operations",
        )
        self.assertEqual(context.summary["prepared_actions"], [])
        self.assertIn("Prepared today's law-firm Reel content plan", context.summary["internal_memory_tasks"])
        self.assertIn("Blocked branded image generation", context.summary["blocked_actions"])
        self.assertIn("Blocked Instagram publishing", context.summary["blocked_actions"])
        self.assertIn("connector_execution", context.summary)
        completion = context.summary["autonomous_work_completion_rate"]
        self.assertEqual(completion["metric"], "Autonomous Work Completion Rate")
        self.assertEqual(completion["planned_tasks"], 4)
        self.assertEqual(completion["completed_automatically"], 0)
        self.assertEqual(completion["blocked"], 4)
        self.assertEqual(completion["success_rate_percent"], 0)
        self.assertEqual(completion["target_success_rate_percent"], 95)
        influence = context.summary["revenue_influence_score"]
        self.assertEqual(influence["metric"], "Revenue Influence Score")
        self.assertEqual(influence["status"], "unavailable")
        self.assertIn("post", influence["traceability_required"])
        self_evaluation = context.summary["self_evaluation"]
        self.assertEqual(self_evaluation["did_create_measurable_business_value_today"], "no")
        self.assertIn("Did I create measurable business value today?", self_evaluation["questions"])
        self.assertIn("closed-loop attribution", self_evaluation["highest_impact_blocker"])
        self.assertEqual(
            self_evaluation["optimization_principle"],
            "Never optimize activity. Always optimize customer acquisition.",
        )

    def test_file_output_writes_daily_action_memory(self) -> None:
        context = _context()
        with tempfile.TemporaryDirectory() as workforce_tmp:
            output = MarketingDepartment(
                company_config=_company_config(),
                objectives_config=_objectives_config(),
                timezone="Asia/Jerusalem",
                memory_root=Path(workforce_tmp),
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
            executions_path = result.paths["executions"]
            actions = json.loads(actions_path.read_text(encoding="utf-8"))
            executions = json.loads(executions_path.read_text(encoding="utf-8"))

        self.assertTrue(actions_path.name.endswith(".json"))
        self.assertEqual(len(actions), 8)
        self.assertTrue(any(item["connector"] == "ImageExecutor" for item in executions))
        self.assertTrue(all(item["status"] in {"completed", "blocked", "failed"} for item in executions))
        self.assertEqual(actions[0]["initiative"], "Acquire the first three paying law firms")
        self.assertIn("delegated_authority_used", actions[0])

    def test_autonomous_work_completion_rate_counts_completed_connector_work(self) -> None:
        context = _context()
        with tempfile.TemporaryDirectory() as tmpdir:
            output = MarketingDepartment(
                company_config=_company_config(),
                objectives_config=_objectives_config(),
                timezone="Asia/Jerusalem",
                social_publishing_enabled=True,
                buffer_access_token="token",
                buffer_profile_id="profile",
                execution_dry_run=True,
                memory_root=Path(tmpdir),
            ).run(context)
        attach_marketing_department_output(context, output)

        completion = context.summary["autonomous_work_completion_rate"]

        self.assertEqual(completion["planned_tasks"], 4)
        self.assertEqual(completion["completed_automatically"], 0)
        self.assertEqual(completion["blocked"], 4)
        self.assertEqual(completion["success_rate"], 0)


if __name__ == "__main__":
    unittest.main()
