from pathlib import Path
import unittest


class CEOConstitutionTests(unittest.TestCase):
    def test_constitution_contains_delegated_authority_and_trust_rules(self) -> None:
        content = Path("knowledge/ceo_constitution.md").read_text(encoding="utf-8")

        self.assertIn("delegated authority", content)
        self.assertIn("Never sacrifice customer trust", content)
        self.assertIn("Educate first", content)
        self.assertIn("highest-impact action", content)


if __name__ == "__main__":
    unittest.main()
