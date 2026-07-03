from pathlib import Path
from types import SimpleNamespace
import json
import unittest

from src.channels.base import OutputResult
from src.main import GeneratedBrief, _email_payload


class EmailPayloadTests(unittest.TestCase):
    def test_email_payload_is_valid_json(self) -> None:
        generated = GeneratedBrief(
            company_config={
                "company": {
                    "name": "ChatBot2U",
                    "recipient_email": "rami@gateco.ai",
                }
            },
            decision_context=SimpleNamespace(run_date="2026-07-03"),
            brief="### בריף\n\nפניות חדשות דרך WhatsApp.",
        )
        result = OutputResult(
            channel="file",
            paths={
                "brief": Path("memory/briefs/2026-07-03.md"),
                "report": Path("memory/reports/2026-07-03.json"),
            },
            message="saved",
        )

        payload = _email_payload(generated, result)
        encoded = json.dumps(payload, ensure_ascii=False)
        decoded = json.loads(encoded)

        self.assertEqual(decoded["to"], "rami@gateco.ai")
        self.assertEqual(decoded["subject"], "📊 ChatBot2U CEO Daily Brief – 2026-07-03")
        self.assertIn("body_markdown", decoded)
        self.assertEqual(decoded["brief_path"], "memory/briefs/2026-07-03.md")
        self.assertEqual(decoded["report_path"], "memory/reports/2026-07-03.json")


if __name__ == "__main__":
    unittest.main()
