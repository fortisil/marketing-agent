from __future__ import annotations

import json
import unittest

from src.providers.meta_graph import MetaGraphProvider


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


class MetaGraphProviderTests(unittest.TestCase):
    def test_missing_credentials_returns_unavailable_status(self) -> None:
        provider = MetaGraphProvider(
            access_token="",
            ad_account_id="1011149454836521",
            ig_account_id="",
            api_version="v23.0",
            timezone="Asia/Jerusalem",
        )

        snapshot = provider.collect()

        self.assertFalse(snapshot.metrics["meta_ads"]["available"])
        self.assertIn("META_ACCESS_TOKEN", snapshot.metrics["meta_ads"]["reason"])

    def test_collects_account_campaign_insights_and_instagram_media(self) -> None:
        def fake_urlopen(url: str) -> FakeResponse:
            if "/act_1011149454836521?" in url:
                return FakeResponse({"id": "act_1011149454836521", "name": "ChatBot2U Ads"})
            if "/campaigns?" in url:
                return FakeResponse(
                    {
                        "data": [
                            {
                                "id": "cmp_1",
                                "name": "Demo campaign",
                                "status": "ACTIVE",
                                "effective_status": "ACTIVE",
                            }
                        ]
                    }
                )
            if "/adsets?" in url:
                return FakeResponse({"data": []})
            if "/ads?" in url:
                return FakeResponse({"data": []})
            if "/insights?" in url and "act_1011149454836521" in url:
                return FakeResponse(
                    {
                        "data": [
                            {
                                "spend": "19.5",
                                "impressions": "1000",
                                "reach": "800",
                                "clicks": "40",
                                "ctr": "4.0",
                                "actions": [{"action_type": "link_click", "value": "40"}],
                            }
                        ]
                    }
                )
            if "/1789/media?" in url:
                return FakeResponse(
                    {
                        "data": [
                            {
                                "id": "media_1",
                                "caption": "Book a demo via WhatsApp",
                                "permalink": "https://instagram.com/p/demo",
                                "media_type": "IMAGE",
                                "comments_count": 3,
                                "like_count": 21,
                            }
                        ]
                    }
                )
            if "/media_1/insights?" in url:
                return FakeResponse({"data": [{"name": "reach", "values": [{"value": 400}]}]})
            return FakeResponse({"data": []})

        provider = MetaGraphProvider(
            access_token="token",
            ad_account_id="1011149454836521",
            ig_account_id="1789",
            api_version="v23.0",
            timezone="Asia/Jerusalem",
            urlopen=fake_urlopen,
        )

        snapshot = provider.collect()
        meta = snapshot.metrics["meta_ads"]

        self.assertTrue(meta["available"])
        self.assertEqual(meta["campaigns_summary"]["active"][0]["name"], "Demo campaign")
        self.assertEqual(meta["today"]["spend"], 19.5)
        self.assertEqual(meta["today"]["impressions"], 1000)
        self.assertTrue(meta["instagram"]["available"])
        self.assertEqual(meta["instagram"]["recent_media"][0]["comments_count"], 3)


if __name__ == "__main__":
    unittest.main()
