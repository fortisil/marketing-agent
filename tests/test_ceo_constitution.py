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
        self.assertIn("This capability increases the probability", content)
        self.assertIn("Did I create measurable business value today?", content)
        self.assertIn("Business Memory", content)

    def test_autonomous_cmo_acceptance_spec_defines_done_by_business_growth(self) -> None:
        content = Path("AUTONOMOUS_CMO_ACCEPTANCE.md").read_text(encoding="utf-8")

        self.assertIn("not evaluated by the quality of its reports", content)
        self.assertIn("30 consecutive days", content)
        self.assertIn("Content Intelligence", content)
        self.assertIn("Marketing Attribution", content)
        self.assertIn("Business Scoreboard", content)
        self.assertIn("additional paying customers", content)
        self.assertIn("No mock data in production", content)
        self.assertIn("Executive Calendar", content)
        self.assertIn("Hypothesis Register", content)
        self.assertIn("Business Memory", content)
        self.assertIn("Never optimize likes", content)

    def test_operational_readiness_audit_defines_unattended_run_gaps(self) -> None:
        content = Path("OPERATIONAL_READINESS.md").read_text(encoding="utf-8")

        self.assertIn("Production readiness: 61%", content)
        self.assertIn("Status: Not ready for unattended 30-day operation.", content)
        self.assertIn("Capability Scorecard", content)
        self.assertIn("Budget Control Audit", content)
        self.assertIn("Failure Recovery Audit", content)
        self.assertIn("Evidence Verification Audit", content)
        self.assertIn("Go for unattended 30-day operation", content)
        self.assertIn("MetaExecutor", content)
        self.assertIn("WhatsApp event webhook", content)
        self.assertIn("What prevents the AI CMO from acquiring another paying customer", content)
        self.assertIn("Investor-Style Priority Stack", content)
        self.assertIn("Closed-loop attribution", content)
        self.assertIn("Autonomy Risks", content)
        self.assertIn("Executive Calendar Gap", content)
        self.assertIn("Sunday Audit Update Requirement", content)


if __name__ == "__main__":
    unittest.main()
