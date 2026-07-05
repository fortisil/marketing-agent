from pathlib import Path
import unittest


class CEOConstitutionTests(unittest.TestCase):
    def test_constitution_contains_delegated_authority_and_trust_rules(self) -> None:
        content = Path("knowledge/ceo_constitution.md").read_text(encoding="utf-8")

        self.assertIn("measurable improvement it creates in the business", content)
        self.assertIn("delegated authority", content)
        self.assertIn("Never sacrifice customer trust", content)
        self.assertIn("Educate first", content)
        self.assertIn("highest-impact action", content)

    def test_autonomous_cmo_acceptance_spec_defines_done_by_business_growth(self) -> None:
        content = Path("AUTONOMOUS_CMO_ACCEPTANCE.md").read_text(encoding="utf-8")

        self.assertIn("not evaluated by the quality of its reports", content)
        self.assertIn("30 consecutive days", content)
        self.assertIn("Content Intelligence", content)
        self.assertIn("Marketing Attribution", content)
        self.assertIn("Business Scoreboard", content)
        self.assertIn("additional paying customers", content)
        self.assertIn("No mock data in production", content)


if __name__ == "__main__":
    unittest.main()
