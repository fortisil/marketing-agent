from __future__ import annotations

import unittest

from src.main import _generated_asset_artifacts, _published_business_artifacts


class MarketingAcceptanceTests(unittest.TestCase):
    def test_generated_image_is_not_a_published_business_artifact(self) -> None:
        results = [
            {
                "status": "completed",
                "action": "generate_branded_social_image",
                "proof": {
                    "public_url": "https://res.cloudinary.com/demo/image/upload/image.png",
                    "sha256": "a" * 64,
                    "worker_id": "marketing-design-worker-1",
                },
            }
        ]

        self.assertEqual(_generated_asset_artifacts(results)[0]["type"], "branded_image")
        self.assertEqual(_published_business_artifacts(results), [])

    def test_buffer_publish_with_required_evidence_is_business_artifact(self) -> None:
        results = [
            {
                "status": "completed",
                "action": "publish_social_post",
                "timestamp": "2026-07-05T19:00:00+03:00",
                "proof": {
                    "buffer_update_id": "update_123",
                    "instagram_url": "https://www.instagram.com/p/test/",
                    "caption_hash": "a" * 64,
                    "image_sha256": "b" * 64,
                    "worker_id": "marketing-social-worker-1",
                },
            }
        ]

        artifacts = _published_business_artifacts(results)

        self.assertEqual(artifacts[0]["type"], "instagram_post")
        self.assertEqual(artifacts[0]["buffer_update_id"], "update_123")


if __name__ == "__main__":
    unittest.main()
