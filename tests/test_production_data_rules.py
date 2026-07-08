from __future__ import annotations

import unittest
from datetime import datetime
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from src.briefs.generator import (
    _ensure_executive_opening,
    build_prompt,
    validate_executive_decision_brief_style,
)
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
        self.assertIn("Executive Decision Brief", prompt)
        self.assertIn("Yesterday the business became healthier because", prompt)
        self.assertIn("Yesterday the business did not improve because", prompt)
        self.assertIn("The Executive OS is not evaluated by activities", prompt)
        self.assertIn("Every morning the AI must prove that the probability of acquiring another paying customer increased", prompt)
        self.assertIn("executive_measurement", prompt)
        self.assertIn("operating_executive", prompt)
        self.assertIn("Never leave the CEO with a bare \"Unavailable\" row", prompt)
        self.assertIn("Did it manage the business today?", prompt)
        self.assertIn("Every department manager permanently owns business assets", prompt)
        self.assertIn("operating_executive.manager_reports", prompt)
        self.assertIn("operating_executive.internal_budget_ledger", prompt)
        self.assertIn("Budget is internally authoritative", prompt)
        self.assertIn("Use three evidence levels", prompt)
        self.assertIn("What improved? Why? What got worse?", prompt)
        self.assertIn("Executive Decision", prompt)
        self.assertIn("Manager Performance", prompt)
        self.assertIn("Are we closer to another paying customer than we were yesterday?", prompt)
        self.assertIn("EXECUTIVE SCOREBOARD", prompt)
        self.assertIn("Business Health must never be unavailable", prompt)
        self.assertIn("Business Funnel", prompt)
        self.assertIn("Content Intelligence", prompt)
        self.assertIn("Campaign Intelligence", prompt)
        self.assertIn("Website Intelligence", prompt)
        self.assertIn("Competitor Intelligence", prompt)
        self.assertIn("WhatsApp Intelligence", prompt)
        self.assertIn("Decision Ledger", prompt)
        self.assertIn("Opportunity Ranking", prompt)
        self.assertIn("Do not list the mission as the opportunity", prompt)
        self.assertIn("Executive Calendar", prompt)
        self.assertIn("If I were the CEO today", prompt)
        self.assertIn("No paragraphs", prompt)
        self.assertIn("No verified data available yet", prompt)
        self.assertIn("Data confidence:", prompt)
        self.assertIn("not an activity log", prompt)
        self.assertIn("executive dashboard", prompt)
        self.assertIn("execution_queue", prompt)
        self.assertIn("marketing_department", prompt)
        self.assertIn("connector_execution", prompt)
        self.assertIn("autonomous_work_completion_rate", prompt)
        self.assertIn("revenue_influence_score", prompt)
        self.assertIn("business_autonomy_index", prompt)
        self.assertIn("growth_intelligence", prompt)
        self.assertIn("promotion_brain", prompt)
        self.assertIn("budget_status", prompt)
        self.assertIn("budget_guard", prompt)
        self.assertIn("content_intelligence", prompt)
        self.assertIn("decision_ledger", prompt)
        self.assertIn("hypothesis_register", prompt)
        self.assertIn("business_memory", prompt)
        self.assertIn("monitoring", prompt)
        self.assertIn("weekly_executive_review", prompt)
        self.assertIn("acceptance_criteria", prompt)
        self.assertIn("final_definition_of_done", prompt)
        self.assertIn("workforce", prompt)
        self.assertIn("Include budget status only as operating proof", prompt)
        self.assertIn("Include learning only from `growth_intelligence`, `content_intelligence`, `hypothesis_register`, `decision_ledger`, and `business_memory`", prompt)
        self.assertIn("Include promotion only from `promotion_brain` and `budget_guard`", prompt)
        self.assertIn("The brief must include a section titled exactly \"Campaign Decision\"", prompt)
        self.assertIn("CEO Action Required must be exactly Yes or No", prompt)
        self.assertIn("Use `monitoring` for health status", prompt)
        self.assertIn("If there is no evidence, the action did not happen.", prompt)
        self.assertIn("Buffer update ID, Buffer post URL, publish status, timestamp, caption hash, image hash, and worker ID", prompt)
        self.assertIn("Include an Instagram permalink only when Buffer returns a real `instagram.com` URL.", prompt)
        self.assertIn("Do not claim content was published", prompt)
        self.assertIn("Do not tell the CEO that something is \"ready\"", prompt)
        self.assertIn("Never write phrases like \"publishing path exists\"", prompt)
        self.assertIn("Only report: Completed, Blocked, Failed", prompt)
        self.assertIn("Do not include long internal task lists", prompt)
        self.assertNotIn("כתוב בריף", prompt)

    def test_executive_decision_brief_validator_rejects_activity_log_opening(self) -> None:
        brief = "I published one post yesterday.\n\n## EXECUTIVE SCOREBOARD"

        with self.assertRaisesRegex(RuntimeError, "business-health sentence"):
            validate_executive_decision_brief_style(brief)

    def test_executive_opening_is_inserted_from_structured_measurement(self) -> None:
        context = SimpleNamespace(
            summary={
                "executive_measurement": {
                    "business_health": {
                        "trend": "flat",
                        "reason": [
                            "- WhatsApp attribution is missing, so customer acquisition cannot be measured.",
                        ],
                    },
                },
            }
        )

        brief = _ensure_executive_opening("## Executive Decision\nNo verified result yet.", context)

        self.assertTrue(
            brief.startswith(
                "Yesterday the business did not improve because WhatsApp attribution is missing"
            )
        )

    def test_executive_opening_uses_improving_business_health(self) -> None:
        context = SimpleNamespace(
            summary={
                "executive_measurement": {
                    "business_health": {
                        "status": "improving",
                        "trend": "improving",
                        "reason": [
                            "+ Published customer-acquisition content with execution proof.",
                        ],
                    },
                },
            }
        )

        brief = _ensure_executive_opening("## Executive Decision\nMarket proof is under review.", context)

        self.assertTrue(
            brief.startswith(
                "Yesterday the business became healthier because published customer-acquisition content"
            )
        )

    def test_executive_decision_brief_validator_rejects_bare_unavailable_rows(self) -> None:
        brief = """
Yesterday the business did not improve because no verified customer-acquisition outcome was available yet.

## Executive Decision
No decision can be made until the missing signal is reviewed.

## EXECUTIVE SCOREBOARD
Business Health ............. 64

## Manager Performance
Social Manager: status monitoring; KPI pending; next review 16:00.

## Executive Summary
- No verified data available yet.

## Yesterday
None completed with proof.

## Results
Unavailable

## Business Funnel
Reach -> Clicks -> WhatsApp -> Qualified -> Demo -> Customer.

## Content Intelligence
No data because insights are not connected; I will review at 16:00.

## Campaign Intelligence
Blocked because budget guard lacks verified spend; campaign plan is defined.

## Website Intelligence
No click data because analytics is not connected; review pending.

## Competitor Intelligence
No monitor connected; using public platform hypotheses.

## WhatsApp Intelligence
No webhook connected; waiting for event-log deployment.

## Decision Ledger
No autonomous spend decision without attribution.

## Currently Working
Discovering the missing attribution path.

## Self Evaluation
Yesterday's prediction: unavailable. Result: unavailable.

## Business Memory
No verified learning added.

## Budget
Daily: no verified spend; guard blocks promotion.

## Opportunity Ranking
1. Founder video because it has highest predicted conversion.

## Risks
Closed-loop attribution missing.

## Executive Calendar
09:00 Review verified data availability.

## Proof
No completed action proof available.

If I were the CEO today, I would focus on: attribution because it tells us which action creates paying customers.
"""

        with self.assertRaisesRegex(RuntimeError, "bare unavailable"):
            validate_executive_decision_brief_style(brief)

    def test_executive_decision_brief_validator_accepts_business_first_brief(self) -> None:
        brief = """
Yesterday the business did not improve because no verified customer-acquisition outcome was available yet.

## Executive Decision
Yesterday no measurable customer-acquisition result was proven; today I will remove the measurement blocker and review the decision again by 16:00.

## EXECUTIVE SCOREBOARD
Business Health ............. 64 / 100, requires attention

## Manager Performance
Social Manager: monitoring Instagram and Facebook; KPI Business Value Score 62; next review 16:00.
Ads Manager: owns Meta Ads, Budget, Campaigns; decision hold spend until guardrails pass.
Analytics Manager: owns attribution; risk no closed-loop measurement.
Website Manager: owns homepage and CTA conversion.
Creative Director: owns creative quality.
Growth Manager: owns opportunity ranking.

## Executive Summary
- No verified data available yet.

## Yesterday
None completed with proof.

## Results
No verified data available yet because attribution is not connected; business impact is unknown conversion; automatic action is to connect attribution and review by 16:00; confidence 64%.

## Business Funnel
Reach -> Clicks -> WhatsApp -> Qualified -> Demo -> Customer.

## Content Intelligence
No verified post-performance data because Instagram Insights is not connected; continue monitoring and review in 6 hours.

## Campaign Intelligence
Campaign is blocked by budget guard; if Meta becomes available launch Israeli law-firm WhatsApp objective at ₪20/day with ₪80 stop rule.

## Campaign Decision
- Decision: retry_later
- Reason: Meta connector is missing.
- Budget: ₪20/day, ₪600/month.
- Status: Campaign failed and automatic retry scheduled.
- Next Automatic Action: Retry Meta connector validation.
- Retry Time: 2026-07-07 16:00 Asia/Jerusalem
- CEO Action Required: No
- Evidence: Rules checked; Failed rules: meta_connector_available; Next retry time: 2026-07-07 16:00 Asia/Jerusalem.

## Website Intelligence
No verified click data because website analytics is not connected; review CTA path and open a PR if friction is found.

## Competitor Intelligence
No competitor monitor connected; use public platform hypotheses until monitoring exists.

## WhatsApp Intelligence
No verified WhatsApp event data available.

## Decision Ledger
No autonomous spend decision without attribution.

## Currently Working
Discovering the missing attribution path.

## Self Evaluation
Yesterday's prediction: unavailable. Result: unavailable.

## Business Memory
No verified learning added.

## Budget
Daily: unavailable. Monthly: unavailable.

## Opportunity Ranking
1. Connect attribution.

## Risks
Closed-loop attribution missing.

## Executive Calendar
09:00 Review verified data availability.

## Proof
No completed action proof available.

If I were the CEO today, I would focus on: attribution because it tells us which action creates paying customers.
"""

        validate_executive_decision_brief_style(brief)


if __name__ == "__main__":
    unittest.main()
