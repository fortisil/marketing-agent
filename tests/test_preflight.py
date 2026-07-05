from __future__ import annotations

from contextlib import redirect_stdout
import io
from pathlib import Path
import tempfile
import unittest

from src.config import Settings
from src.main import preflight


def _settings(**overrides: object) -> Settings:
    with tempfile.TemporaryDirectory() as tmpdir:
        base = {
            "app_env": "production",
            "allow_mock_data": False,
            "openai_api_key": "openai",
            "openai_model": "gpt-4o-mini",
            "brief_language": "en",
            "company_config_path": Path("config/companies/chatbot2u.yaml"),
            "objectives_config_path": Path("config/objectives/chatbot2u.yaml"),
            "funnel_config_path": Path("config/funnels/chatbot2u.yaml"),
            "ceo_constitution_path": Path("knowledge/ceo_constitution.md"),
            "knowledge_path": Path("knowledge/chatbot2u.md"),
            "brand_root": Path("knowledge/companies/chatbot2u/brand"),
            "assets_root": Path("assets/companies/chatbot2u"),
            "hebrew_style_guide_path": Path("knowledge/hebrew_style_guide.md"),
            "chatbot2u_repo_path": None,
            "memory_path": Path(tmpdir),
            "log_level": "ERROR",
            "timezone": "Asia/Jerusalem",
            "brief_hour": 8,
            "brief_minute": 0,
            "gmail_credentials_file": Path("secrets/gmail_credentials.json"),
            "gmail_token_file": Path("secrets/gmail_token.json"),
            "gmail_sender": "",
            "email_channel_enabled": False,
            "resend_api_key": "resend",
            "email_from": "cmo@gateco.ai",
            "email_to": "rami@gateco.ai",
            "meta_access_token": "",
            "meta_ad_account_id": "1011149454836521",
            "meta_ig_account_id": "",
            "meta_api_version": "v23.0",
            "whatsapp_provider": "webhook",
            "whatsapp_events_path": None,
            "whatsapp_webhook_url": "",
            "social_publishing_enabled": True,
            "buffer_access_token": "buffer",
            "buffer_profile_id": "profile",
            "execution_dry_run": False,
            "image_generation_enabled": True,
            "openai_image_model": "gpt-image-1",
            "asset_public_base_url": "",
            "asset_upload_provider": "cloudinary",
            "cloudinary_cloud_name": "cloud",
            "cloudinary_api_key": "key",
            "cloudinary_api_secret": "secret",
            "meta_execution_enabled": False,
        }
        base.update(overrides)
        return Settings(**base)


class PreflightTests(unittest.TestCase):
    def test_preflight_ready_with_cloudinary_public_upload(self) -> None:
        payload = _silent_preflight(_settings())

        self.assertTrue(payload["ready_for_tomorrow"])
        self.assertEqual(payload["blocking_issues"], [])
        self.assertTrue(payload["required_vars"]["ASSET_PUBLIC_BASE_URL"]["ok"])
        self.assertTrue(payload["required_secrets"]["BUFFER_ACCESS_TOKEN"]["configured"])
        self.assertTrue(payload["workflows"]["daily-brief.yml"]["ok"])

    def test_preflight_blocks_dry_run_and_missing_secret(self) -> None:
        payload = _silent_preflight(
            _settings(
                buffer_access_token="",
                execution_dry_run=True,
            )
        )

        self.assertFalse(payload["ready_for_tomorrow"])
        self.assertFalse(payload["required_secrets"]["BUFFER_ACCESS_TOKEN"]["configured"])
        self.assertFalse(payload["required_vars"]["EXECUTION_DRY_RUN"]["ok"])
        self.assertTrue(
            any("BUFFER_ACCESS_TOKEN" in issue for issue in payload["blocking_issues"])
        )


def _silent_preflight(settings: Settings) -> dict[str, object]:
    with redirect_stdout(io.StringIO()):
        return preflight(settings)


if __name__ == "__main__":
    unittest.main()
