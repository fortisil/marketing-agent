import unittest

from src.briefs.generator import normalize_brief_language, validate_hebrew_brief_style


class HebrewStyleTests(unittest.TestCase):
    def test_normalize_brief_language_removes_bad_terms(self) -> None:
        brief = "נגנבו 8 לידים דרך WattsApp. שלחו הודעה ב-WattsApp."

        normalized = normalize_brief_language(brief)

        self.assertNotIn("נגנבו", normalized)
        self.assertNotIn("WattsApp", normalized)
        self.assertIn("WhatsApp", normalized)

    def test_validate_hebrew_brief_style_accepts_clean_whatsapp_copy(self) -> None:
        validate_hebrew_brief_style("התקבלו פניות חדשות דרך WhatsApp.")

    def test_normalize_brief_language_fixes_funnel_label_and_awkward_hebrew(self) -> None:
        brief = "Today's bottledneck: נמוך. צריך לחומש את הפניות ולהמריא את הדמו."

        normalized = normalize_brief_language(brief)

        self.assertIn("Today's bottleneck", normalized)
        self.assertIn("להגדיל את הפניות", normalized)
        self.assertNotIn("לחומש", normalized)


if __name__ == "__main__":
    unittest.main()
