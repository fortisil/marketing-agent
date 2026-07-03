from __future__ import annotations

import json
import unittest

from src.decisions.engine import DecisionEngine
from src.providers.base import MetricSnapshot
from src.providers.marketing_platform import MarketingPlatformProvider
from tests.test_meta_ads_provider import FakeResponse


class MarketingPlatformProviderTests(unittest.TestCase):
    def test_meta_mcp_returns_required_actions(self) -> None:
        provider = MarketingPlatformProvider(
            company_config={
                "marketing_platform": {
                    "provider": "meta_mcp",
                    "fallback_provider": "meta_graph",
                    "meta_ad_account_id": "1011149454836521",
                    "instagram_username": "chatbot2u",
                }
            },
            access_token="",
            env_ad_account_id="1011149454836521",
            ig_account_id="",
            api_version="v23.0",
            timezone="Asia/Jerusalem",
        )

        snapshot = provider.collect()
        platform = snapshot.metrics["marketing_platform"]

        self.assertEqual(platform["provider"], "meta_mcp")
        self.assertEqual(platform["fallback_provider"], "meta_graph")
        self.assertFalse(platform["metrics_available"])
        self.assertTrue(platform["mcp"]["requires_external_mcp_execution"])
        self.assertIn("Call Meta MCP ads_get_ad_accounts", platform["mcp_required_actions"])

    def test_meta_mcp_falls_back_to_graph_when_credentials_exist(self) -> None:
        def fake_urlopen(url: str) -> FakeResponse:
            if "/act_1011149454836521?" in url:
                return FakeResponse({"id": "act_1011149454836521", "name": "ChatBot2U Ads"})
            if "/campaigns?" in url:
                return FakeResponse({"data": []})
            if "/adsets?" in url:
                return FakeResponse({"data": []})
            if "/ads?" in url:
                return FakeResponse({"data": []})
            if "/insights?" in url:
                return FakeResponse({"data": [{"spend": "3", "impressions": "100", "reach": "90", "clicks": "5", "ctr": "5"}]})
            return FakeResponse({"data": []})

        provider = MarketingPlatformProvider(
            company_config={
                "marketing_platform": {
                    "provider": "meta_mcp",
                    "fallback_provider": "meta_graph",
                    "meta_ad_account_id": "1011149454836521",
                    "instagram_username": "chatbot2u",
                }
            },
            access_token="token",
            env_ad_account_id="1011149454836521",
            ig_account_id="",
            api_version="v23.0",
            timezone="Asia/Jerusalem",
            urlopen=fake_urlopen,
        )

        snapshot = provider.collect()
        platform = snapshot.metrics["marketing_platform"]

        self.assertTrue(platform["metrics_available"])
        self.assertTrue(platform["graph_api_status"]["available"])
        self.assertEqual(platform["meta_ads"]["today"]["spend"], 3.0)
        self.assertTrue(platform["mcp"]["requires_external_mcp_execution"])

    def test_decision_engine_describes_mcp_without_disconnected_language(self) -> None:
        provider = MarketingPlatformProvider(
            company_config={
                "company": {"name": "ChatBot2U"},
                "marketing_platform": {
                    "provider": "meta_mcp",
                    "fallback_provider": "meta_graph",
                    "meta_ad_account_id": "1011149454836521",
                    "instagram_username": "chatbot2u",
                },
            },
            access_token="",
            env_ad_account_id="1011149454836521",
            ig_account_id="",
            api_version="v23.0",
            timezone="Asia/Jerusalem",
        )
        platform_snapshot = provider.collect()
        mock_snapshot = MetricSnapshot(
            provider="mock",
            collected_at=platform_snapshot.collected_at,
            metrics={
                "booked_demos": 1,
                "target_booked_demos": 3,
                "qualified_leads": 4,
                "whatsapp_clicks": 10,
                "estimated_spend_ils": 0,
            },
        )

        decision_context = DecisionEngine(
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
        ).evaluate([mock_snapshot, platform_snapshot])
        decision_text = json.dumps(decision_context.to_prompt_payload(), ensure_ascii=False)

        self.assertIn("Meta MCP is the preferred execution layer", decision_text)
        self.assertIn("Use ChatGPT/Meta MCP to fetch live metrics", decision_text)
        self.assertNotIn("Meta is disconnected", decision_text)


if __name__ == "__main__":
    unittest.main()
