from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from src.agents.design_system import DesignSystemAgent
from src.providers.brand import BrandProvider


class BrandBrainTests(unittest.TestCase):
    def test_brand_provider_loads_company_brand_library(self) -> None:
        provider = BrandProvider(
            company_config={"company": {"name": "ChatBot2U"}},
            timezone="Asia/Jerusalem",
            brand_root=Path("knowledge/companies/chatbot2u/brand"),
            assets_root=Path("assets/companies/chatbot2u"),
        )

        snapshot = provider.collect()
        brand = snapshot.metrics["brand_intelligence"]

        self.assertTrue(brand["available"])
        self.assertEqual(brand["source"], "brand_library")
        self.assertEqual(brand["colors"]["primary"], "#0F62FE")
        self.assertIn("logo-dark.svg", brand["logos"]["preferred"])
        self.assertEqual(brand["brand"]["internal_language"], "English")
        self.assertEqual(brand["brand"]["marketing_language"], "Hebrew")
        self.assertEqual(brand["brand"]["default_post_language"], "Hebrew")
        self.assertEqual(brand["cta"]["link"], "https://wa.me/972559720244")
        self.assertTrue(brand["cta"]["required_in_posts"])
        self.assertEqual(brand["image_generation"]["provider"], "openai")
        self.assertEqual(brand["image_generation"]["model"], "gpt-image-1")
        self.assertEqual(brand["image_generation"]["text_policy"], "no_model_rendered_text")
        self.assertEqual(brand["video_generation"]["provider"], "heygen")
        self.assertEqual(brand["video_generation"]["aspect_ratio"], "9:16")
        self.assertFalse(brand["video_generation"]["subtitles"])
        self.assertEqual(brand["design_system_review"]["status"], "approved")

    def test_brand_provider_returns_unavailable_when_library_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            provider = BrandProvider(
                company_config={"company": {"name": "ChatBot2U"}},
                timezone="Asia/Jerusalem",
                brand_root=Path(tmpdir) / "missing",
                assets_root=Path(tmpdir) / "assets",
            )

            snapshot = provider.collect()

        brand = snapshot.metrics["brand_intelligence"]
        self.assertFalse(brand["available"])
        self.assertEqual(brand["source"], "missing_brand_library")

    def test_design_system_agent_rejects_missing_brand(self) -> None:
        review = DesignSystemAgent().review_brand({"available": False})

        self.assertEqual(review["status"], "needs_regeneration")
        self.assertIn("must not guess", review["reason"])


if __name__ == "__main__":
    unittest.main()
