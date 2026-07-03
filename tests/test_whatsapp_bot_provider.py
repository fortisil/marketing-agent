from __future__ import annotations

from datetime import datetime
from pathlib import Path
import unittest
from io import BytesIO
from unittest.mock import patch
from zoneinfo import ZoneInfo

from src.providers.whatsapp_bot import WhatsAppBotProvider


class WhatsAppBotProviderTests(unittest.TestCase):
    def test_mock_mode_returns_funnel_intelligence(self) -> None:
        provider = WhatsAppBotProvider(provider="mock", timezone="Asia/Jerusalem")

        fixed_now = datetime(2026, 7, 3, 14, 0, tzinfo=ZoneInfo("Asia/Jerusalem"))
        with patch("src.providers.whatsapp_bot.datetime") as mocked_datetime:
            mocked_datetime.now.return_value = fixed_now
            mocked_datetime.fromisoformat.side_effect = datetime.fromisoformat
            mocked_datetime.min = datetime.min
            snapshot = provider.collect()

        metrics = snapshot.metrics["whatsapp_bot"]

        self.assertTrue(metrics["available"])
        self.assertEqual(metrics["provider"], "mock")
        self.assertEqual(metrics["today"]["conversations"], 4)
        self.assertEqual(metrics["today"]["qualified_leads"], 2)
        self.assertEqual(metrics["today"]["demo_bookings"], 1)
        self.assertIn("funnel_health_score", metrics["today"])

    def test_missing_json_events_path_returns_unavailable_status(self) -> None:
        provider = WhatsAppBotProvider(
            provider="json_events",
            events_path=None,
            timezone="Asia/Jerusalem",
        )

        snapshot = provider.collect()

        self.assertFalse(snapshot.metrics["whatsapp_bot"]["available"])
        self.assertIn("WHATSAPP_EVENTS_PATH", snapshot.metrics["whatsapp_bot"]["reason"])

    def test_jsonl_fixture_calculates_funnel_metrics(self) -> None:
        provider = WhatsAppBotProvider(
            provider="json_events",
            events_path=Path("tests/fixtures/whatsapp_events.jsonl"),
            timezone="Asia/Jerusalem",
        )

        fixed_now = datetime(2026, 7, 3, 14, 0, tzinfo=ZoneInfo("Asia/Jerusalem"))
        with patch("src.providers.whatsapp_bot.datetime") as mocked_datetime:
            mocked_datetime.now.return_value = fixed_now
            mocked_datetime.fromisoformat.side_effect = datetime.fromisoformat
            mocked_datetime.min = datetime.min
            snapshot = provider.collect()

        metrics = snapshot.metrics["whatsapp_bot"]
        today = metrics["today"]
        last_7_days = metrics["last_7_days"]

        self.assertTrue(metrics["available"])
        self.assertEqual(today["conversations"], 3)
        self.assertEqual(today["qualified_leads"], 2)
        self.assertEqual(today["demo_requests"], 2)
        self.assertEqual(today["demo_bookings"], 1)
        self.assertEqual(today["customers"], 0)
        self.assertEqual(today["average_response_time_seconds"], 4.0)
        self.assertEqual(today["conversion_rates"]["conversation_to_qualified"], 0.6667)
        self.assertEqual(today["conversion_rates"]["qualified_to_demo"], 0.5)
        self.assertEqual(today["conversion_rates"]["conversation_to_demo_booked"], 0.3333)
        self.assertEqual(today["conversion_rates"]["demo_to_customer"], 0.0)
        self.assertEqual(today["bottleneck"], "low_conversation_volume")
        self.assertEqual(last_7_days["conversations"], 4)
        self.assertEqual(last_7_days["demo_bookings"], 2)
        self.assertEqual(last_7_days["customers"], 1)

    def test_webhook_mode_reads_events_payload(self) -> None:
        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return BytesIO(
                    b'[{"timestamp":"2026-07-03T09:00:00+03:00",'
                    b'"conversation_id":"conv_1","phone_hash":"hash",'
                    b'"event":"conversation_started","metadata":{}}]'
                ).read()

        provider = WhatsAppBotProvider(
            provider="webhook",
            webhook_url="https://example.test/events",
            timezone="Asia/Jerusalem",
            urlopen_func=lambda *_args, **_kwargs: FakeResponse(),
        )

        fixed_now = datetime(2026, 7, 3, 14, 0, tzinfo=ZoneInfo("Asia/Jerusalem"))
        with patch("src.providers.whatsapp_bot.datetime") as mocked_datetime:
            mocked_datetime.now.return_value = fixed_now
            mocked_datetime.fromisoformat.side_effect = datetime.fromisoformat
            mocked_datetime.min = datetime.min
            snapshot = provider.collect()

        metrics = snapshot.metrics["whatsapp_bot"]

        self.assertTrue(metrics["available"])
        self.assertEqual(metrics["provider"], "webhook")
        self.assertEqual(metrics["today"]["conversations"], 1)


if __name__ == "__main__":
    unittest.main()
