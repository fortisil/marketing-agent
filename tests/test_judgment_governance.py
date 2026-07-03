from __future__ import annotations

import json
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from src.decisions.engine import DecisionEngine
from src.providers.base import MetricSnapshot


def _engine() -> DecisionEngine:
    return DecisionEngine(
        company_config={
            "company": {"name": "ChatBot2U"},
            "marketing": {
                "primary_kpi": "booked demos",
                "budget_rule": {"amount_ils_per_day": 20},
            },
        },
        objectives_config={
            "company_state": "Validation",
            "north_star_kpi": "booked demos",
            "targets": {"demos_per_week": 3},
            "judgment_scorecard": {
                "dimensions": [
                    {
                        "name": "Judgment",
                        "question": "Would I have made the same decision?",
                        "score_range": "1-10",
                    },
                    {
                        "name": "Business Impact",
                        "question": "Would acting on this likely increase customers?",
                        "score_range": "1-10",
                    },
                    {
                        "name": "Proactivity",
                        "question": "Did it find opportunities on its own?",
                        "score_range": "1-10",
                    },
                    {
                        "name": "Signal vs. Noise",
                        "question": "Was it concise and focused?",
                        "score_range": "1-10",
                    },
                    {
                        "name": "Learning",
                        "question": "Did it improve compared to yesterday?",
                        "score_range": "1-10",
                    },
                ]
            },
            "prediction_policy": {"evaluation_window_days": 7},
            "demo_booking_growth_trend": {"week_1": 3, "week_2": 5, "week_3": 7, "week_4": 9},
            "red_team": {"cadence": "Friday"},
            "success_90_days": {
                "business": [
                    "Demonstrate measurable improvement in lead generation and conversion compared with today's baseline."
                ]
            },
            "governance": {
                "autonomy_principle": "Autonomy grows in proportion to demonstrated performance."
            },
        },
        company_knowledge="ChatBot2U sells WhatsApp automation to Israeli law firms.",
        timezone="Asia/Jerusalem",
    )


class JudgmentGovernanceTests(unittest.TestCase):
    def test_daily_report_contains_judgment_scorecard_and_prediction(self) -> None:
        snapshot = MetricSnapshot(
            provider="whatsapp_bot",
            collected_at=datetime(2026, 7, 3, 8, 0, tzinfo=ZoneInfo("Asia/Jerusalem")),
            metrics={
                "booked_demos": 0,
                "qualified_leads": 1,
                "estimated_spend_ils": 0,
                "whatsapp_bot": {
                    "available": True,
                    "today": {
                        "conversations": 2,
                        "qualified_leads": 1,
                        "demo_bookings": 0,
                        "customers": 0,
                        "bottleneck": "low_conversation_volume",
                        "funnel_health_score": 35,
                    },
                },
            },
        )

        payload = _engine().evaluate([snapshot]).to_prompt_payload()
        report = payload["daily_report"]

        scorecard = report["judgment_scorecard"]
        self.assertEqual(scorecard["principle"], "We are no longer building features. We are building judgment.")
        self.assertEqual(len(scorecard["dimensions"]), 5)
        self.assertIsNone(scorecard["ceo_scores"]["Judgment"])

        prediction = report["prediction"]
        self.assertIn("WhatsApp", prediction["hypothesis"])
        self.assertEqual(prediction["primary_kpi"], "booked demos")
        self.assertEqual(prediction["evaluation_due_date"], report["prediction_evaluation"]["evaluation_due_date"])
        self.assertEqual(report["prediction_evaluation"]["status"], "pending")

        success_status = report["success_90_day_status"]
        self.assertEqual(success_status["business_trend_goal"]["week_4"], 9)
        self.assertIn("autonomy", json.dumps(success_status["governance"], ensure_ascii=False))

    def test_friday_red_team_challenge_is_active(self) -> None:
        engine = _engine()
        challenge = engine._red_team_challenge(
            datetime(2026, 7, 3, 8, 0, tzinfo=ZoneInfo("Asia/Jerusalem")),
            [],
            {},
        )

        self.assertTrue(challenge["active_today"])
        self.assertIn("What evidence", challenge["challenge_question"])
        self.assertIn("counter-hypothesis", challenge["required_response"])


if __name__ == "__main__":
    unittest.main()
