from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from src.memory.journal import write_evening_journal


class ExecutiveJournalTests(unittest.TestCase):
    def test_write_evening_journal_from_latest_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            reports_dir = root / "reports"
            reports_dir.mkdir()
            report = {
                "date": "2026-07-03",
                "metrics": {
                    "whatsapp_bot": {
                        "today_bottleneck": "low_conversation_volume",
                    }
                },
                "recommendations": [{"title": "Increase WhatsApp conversation volume"}],
                "risks": ["Low WhatsApp conversation volume may limit demo bookings."],
                "autonomous_action_log": [
                    {
                        "what_it_did": "Classified task",
                        "why_it_did_it": "Increase demos",
                        "policy_authorized_it": "marketing.publish_posts=always",
                        "expected_outcome": "More demos",
                        "actual_outcome": "planned",
                    }
                ],
            }
            (reports_dir / "2026-07-03.json").write_text(
                json.dumps(report, ensure_ascii=False),
                encoding="utf-8",
            )

            paths = write_evening_journal(root, "Asia/Jerusalem")

            journal = json.loads(paths["journal_json"].read_text(encoding="utf-8"))
            markdown = paths["journal"].read_text(encoding="utf-8")

        self.assertIn("What did I learn today?", markdown)
        self.assertIn("low_conversation_volume", journal["questions"]["what_did_i_learn_today"])
        self.assertEqual(journal["autonomous_action_review"][0]["actual_outcome"], "planned")


if __name__ == "__main__":
    unittest.main()
