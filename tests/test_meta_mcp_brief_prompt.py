from __future__ import annotations

from types import SimpleNamespace
import unittest

from src.briefs.generator import build_prompt


class MetaMcpBriefPromptTests(unittest.TestCase):
    def test_prompt_explains_mcp_without_disconnected_language(self) -> None:
        company_config = {
            "company": {"name": "ChatBot2U"},
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
        decision_context = SimpleNamespace(
            to_prompt_payload=lambda: {
                "summary": {
                    "marketing_platform": {
                        "provider": "meta_mcp",
                        "mcp": {"requires_external_mcp_execution": True},
                    }
                }
            }
        )

        prompt = build_prompt(
            company_config,
            decision_context,
            "Always write professional Hebrew.",
            brief_language="en",
        )

        self.assertIn("Write a daily CEO brief in English", prompt)
        self.assertIn("No campaign has been verified as active.", prompt)
        self.assertNotIn("Meta is disconnected", prompt)
        self.assertNotIn("כתוב בריף", prompt)


if __name__ == "__main__":
    unittest.main()
