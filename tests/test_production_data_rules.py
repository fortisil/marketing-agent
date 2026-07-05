from __future__ import annotations

import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from src.briefs.generator import build_prompt
from src.decisions.engine import DecisionEngine
from src.providers.base import MetricSnapshot
from src.providers.whatsapp_bot import WhatsAppBotProvider


def _company_config() -> dict:
    return {
        "company": {
            "name": "ChatBot2U",
            "recipient_email": "rami@gateco.ai",
            "brief_language": "en",
        },
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
        "mock_data": {
            "booked_demos": 3,
            "qualified_leads": 8,
            "whatsapp_clicks": 31,
        },
    }


def _objectives_config() -> dict:
    return {
        "company_state": "Validation",
        "north_star_kpi": "booked demos",
        "targets": {"demos_per_week": 3},
    }


def _engine() -> DecisionEngine:
    return DecisionEngine(
        company_config=_company_config(),
        objectives_config=_objectives_config(),
        company_knowledge="ChatBot2U sells WhatsApp automation.",
        timezone="Asia/Jerusalem",
    )


class ProductionDataRulesTests(unittest.TestCase):
    def test_production_mode_does_not_allow_mock_whatsapp_metrics(self) -> None:
        provider = WhatsAppBotProvider(provider="mock", app_env="production", allow_mock_data=False)

        snapshot = provider.collect()
        metrics = snapshot.metrics["whatsapp_bot"]

        self.assertFalse(metrics["available"])
        self.assertFalse(metrics["verified"])
        self.assertEqual(metrics["source"], "unavailable")
        self.assertEqual(metrics["today"], {})
        self.assertIn("No verified WhatsApp event data available.", metrics["reason"])
        self.assertIn("connect the WhatsApp bot event log/webhook", metrics["integration_instruction"])
        self.assertEqual(metrics["metric_sources"][0]["value"], None)

    def test_production_decision_context_does_not_show_fake_demo_bookings(self) -> None:
        whatsapp_snapshot = WhatsAppBotProvider(
            provider="mock",
            app_env="production",
            allow_mock_data=False,
        ).collect()
        meta_snapshot = MetricSnapshot(
            provider="marketing_platform",
            collected_at=datetime.now(ZoneInfo("Asia/Jerusalem")),
            metrics={
                "marketing_platform": {
                    "metrics_available": False,
                    "campaign_status": "unknown",
                    "campaign_status_note": "No campaign has been verified as active.",
                },
                "meta_ads": {
                    "available": False,
                    "verified": False,
                    "source": "unavailable",
                    "reason": "No verified Meta campaign data available.",
                    "campaign_status": "unknown",
                    "campaign_status_note": "No campaign has been verified as active.",
                },
            },
            notes=[],
        )

        payload = _engine().evaluate([whatsapp_snapshot, meta_snapshot]).to_prompt_payload()
        summary = payload["summary"]

        self.assertIsNone(summary["booked_demos"])
        self.assertIsNone(summary["qualified_leads"])
        self.assertEqual(summary["data_confidence"]["level"], "Low")
        self.assertEqual(summary["data_confidence"]["reason"], "No verified data available yet.")
        self.assertEqual(summary["executed_actions_today"], ["none"])
        self.assertIn("recommended_actions", summary)

    def test_unavailable_sources_are_named_in_decision_context(self) -> None:
        whatsapp_snapshot = WhatsAppBotProvider(
            provider="mock",
            app_env="production",
            allow_mock_data=False,
        ).collect()
        meta_snapshot = MetricSnapshot(
            provider="marketing_platform",
            collected_at=datetime.now(ZoneInfo("Asia/Jerusalem")),
            metrics={
                "marketing_platform": {"metrics_available": False},
                "meta_ads": {
                    "available": False,
                    "verified": False,
                    "source": "unavailable",
                    "reason": "No verified Meta campaign data available.",
                    "campaign_status": "unknown",
                    "campaign_status_note": "No campaign has been verified as active.",
                },
            },
            notes=[],
        )

        summary = _engine().evaluate([whatsapp_snapshot, meta_snapshot]).summary

        self.assertEqual(
            summary["data_status"]["whatsapp"]["message"],
            "No verified WhatsApp event data available.",
        )
        self.assertEqual(
            summary["data_status"]["meta"]["message"],
            "No verified Meta campaign data available.",
        )
        self.assertEqual(summary["data_status"]["meta"]["campaign_status"], "unknown")
        self.assertEqual(
            summary["data_status"]["meta"]["campaign_status_note"],
            "No campaign has been verified as active.",
        )

    def test_campaign_is_not_reported_active_unless_verified(self) -> None:
        meta_snapshot = MetricSnapshot(
            provider="marketing_platform",
            collected_at=datetime.now(ZoneInfo("Asia/Jerusalem")),
            metrics={
                "meta_ads": {
                    "available": False,
                    "verified": False,
                    "source": "unavailable",
                    "campaign_status": "unknown",
                    "campaign_status_note": "No campaign has been verified as active.",
                }
            },
            notes=[],
        )

        context = _engine().evaluate([meta_snapshot])
        summary = context.summary

        self.assertNotEqual(summary["data_status"]["meta"]["campaign_status"], "active")
        self.assertIn("No campaign has been verified as active.", context.risks)

    def test_ceo_brief_prompt_is_english_when_language_is_en(self) -> None:
        whatsapp_snapshot = WhatsAppBotProvider(
            provider="mock",
            app_env="production",
            allow_mock_data=False,
        ).collect()
        context = _engine().evaluate([whatsapp_snapshot])

        prompt = build_prompt(_company_config(), context, "Hebrew style guide", brief_language="en")

        self.assertIn("Write a daily CEO brief in English", prompt)
        self.assertIn("No verified data available yet", prompt)
        self.assertIn("Data confidence:", prompt)
        self.assertIn("Write like an operator, not a reporter.", prompt)
        self.assertIn("Keep the CEO brief to one page.", prompt)
        self.assertIn("execution_queue", prompt)
        self.assertIn("marketing_department", prompt)
        self.assertIn("connector_execution", prompt)
        self.assertIn("autonomous_work_completion_rate", prompt)
        self.assertIn("revenue_influence_score", prompt)
        self.assertIn("business_autonomy_index", prompt)
        self.assertIn("workforce", prompt)
        self.assertIn("Put `Business Autonomy Index` immediately after the trust banner", prompt)
        self.assertIn("Include `Autonomous Work Completion Rate` after Business Autonomy Index", prompt)
        self.assertIn("Include `Revenue Influence Score` after Autonomous Work Completion Rate", prompt)
        self.assertIn("If there is no evidence, the action did not happen.", prompt)
        self.assertIn("Buffer update ID, Instagram URL, timestamp, caption hash, image hash, and worker ID", prompt)
        self.assertIn("What did I accomplish for ChatBot2U while you were away?", prompt)
        self.assertIn("Do not claim content was published", prompt)
        self.assertIn("Do not tell the CEO that something is \"ready\"", prompt)
        self.assertIn("Never write phrases like \"publishing path exists\"", prompt)
        self.assertIn("Only report: Completed, Blocked, Failed", prompt)
        self.assertIn("Do not include long internal task lists", prompt)
        self.assertNotIn("כתוב בריף", prompt)


if __name__ == "__main__":
    unittest.main()
