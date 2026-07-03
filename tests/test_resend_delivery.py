from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

from src.channels.file_output import FileOutputChannel
from src.channels.email_resend import send_email_resend


class ResendDeliveryTests(unittest.TestCase):
    def test_send_email_resend_uses_mocked_response(self) -> None:
        captured = {}

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return BytesIO(b'{"id":"email_123"}').read()

        def fake_urlopen(request, timeout):
            captured["authorization"] = request.headers["Authorization"]
            captured["payload"] = json.loads(request.data.decode("utf-8"))
            captured["timeout"] = timeout
            return FakeResponse()

        result = send_email_resend(
            api_key="secret_resend_key",
            from_email="AI CMO <briefs@example.com>",
            to_email="rami@gateco.ai",
            subject="Daily Brief",
            body_markdown="### בריף\n\nפניות חדשות דרך WhatsApp.",
            urlopen_func=fake_urlopen,
        )

        self.assertEqual(result["status"], "sent")
        self.assertEqual(result["channel"], "resend")
        self.assertEqual(result["recipient"], "rami@gateco.ai")
        self.assertEqual(result["message_id"], "email_123")
        self.assertEqual(captured["payload"]["subject"], "Daily Brief")
        self.assertIn("פניות חדשות", captured["payload"]["text"])
        self.assertEqual(captured["authorization"], "Bearer secret_resend_key")

    def test_file_output_writes_delivery_status_to_report(self) -> None:
        delivery = {
            "channel": "resend",
            "status": "sent",
            "recipient": "rami@gateco.ai",
            "timestamp": "2026-07-03T08:00:00+03:00",
        }
        daily_report = SimpleNamespace(
            to_dict=lambda: {
                "company": "ChatBot2U",
                "date": "2026-07-03",
                "metrics": {},
            }
        )
        decision_context = SimpleNamespace(
            run_date="2026-07-03",
            daily_report=daily_report,
            to_prompt_payload=lambda: {"run_date": "2026-07-03"},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            result = FileOutputChannel(Path(tmpdir), "Asia/Jerusalem").deliver(
                decision_context=decision_context,
                brief="brief",
                sent=True,
                dry_run=False,
                delivery=delivery,
            )

            report = json.loads(result.paths["report"].read_text(encoding="utf-8"))

        self.assertEqual(report["delivery"], delivery)


if __name__ == "__main__":
    unittest.main()
