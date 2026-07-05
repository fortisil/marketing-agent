from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
from typing import Any, Optional

from dotenv import load_dotenv
import yaml


@dataclass(frozen=True)
class Settings:
    app_env: str
    allow_mock_data: bool
    openai_api_key: str
    openai_model: str
    brief_language: str
    company_config_path: Path
    objectives_config_path: Path
    funnel_config_path: Path
    ceo_constitution_path: Path
    knowledge_path: Path
    brand_root: Path
    assets_root: Path
    hebrew_style_guide_path: Path
    chatbot2u_repo_path: Optional[Path]
    memory_path: Path
    log_level: str
    timezone: str
    brief_hour: int
    brief_minute: int
    gmail_credentials_file: Path
    gmail_token_file: Path
    gmail_sender: str
    email_channel_enabled: bool
    resend_api_key: str
    email_from: str
    email_to: str
    meta_access_token: str
    meta_ad_account_id: str
    meta_ig_account_id: str
    meta_api_version: str
    whatsapp_provider: str
    whatsapp_events_path: Optional[Path]
    whatsapp_webhook_url: str
    social_publishing_enabled: bool
    buffer_access_token: str
    buffer_profile_id: str
    execution_dry_run: bool
    meta_execution_enabled: bool


def load_settings() -> Settings:
    load_dotenv()

    return Settings(
        app_env=os.getenv("APP_ENV", "production").strip().lower() or "production",
        allow_mock_data=os.getenv("ALLOW_MOCK_DATA", "false").lower() == "true",
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        brief_language=os.getenv("BRIEF_LANGUAGE", "en").strip().lower() or "en",
        company_config_path=Path(os.getenv("COMPANY_CONFIG_PATH", "config/companies/chatbot2u.yaml")),
        objectives_config_path=Path(
            os.getenv("OBJECTIVES_CONFIG_PATH", "config/objectives/chatbot2u.yaml")
        ),
        funnel_config_path=Path(os.getenv("FUNNEL_CONFIG_PATH", "config/funnels/chatbot2u.yaml")),
        ceo_constitution_path=Path(os.getenv("CEO_CONSTITUTION_PATH", "knowledge/ceo_constitution.md")),
        knowledge_path=Path(os.getenv("KNOWLEDGE_PATH", "knowledge/chatbot2u.md")),
        brand_root=Path(os.getenv("BRAND_ROOT", "knowledge/companies/chatbot2u/brand")),
        assets_root=Path(os.getenv("ASSETS_ROOT", "assets/companies/chatbot2u")),
        hebrew_style_guide_path=Path(
            os.getenv("HEBREW_STYLE_GUIDE_PATH", "knowledge/hebrew_style_guide.md")
        ),
        chatbot2u_repo_path=(
            Path(os.environ["CHATBOT2U_REPO_PATH"])
            if os.getenv("CHATBOT2U_REPO_PATH")
            else None
        ),
        memory_path=Path(os.getenv("MEMORY_PATH", "memory")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        timezone=os.getenv("APP_TIMEZONE", "Asia/Jerusalem"),
        brief_hour=int(os.getenv("BRIEF_HOUR", "8")),
        brief_minute=int(os.getenv("BRIEF_MINUTE", "0")),
        gmail_credentials_file=Path(os.getenv("GMAIL_CREDENTIALS_FILE", "secrets/gmail_credentials.json")),
        gmail_token_file=Path(os.getenv("GMAIL_TOKEN_FILE", "secrets/gmail_token.json")),
        gmail_sender=os.getenv("GMAIL_SENDER", ""),
        email_channel_enabled=os.getenv("EMAIL_CHANNEL_ENABLED", "false").lower() == "true",
        resend_api_key=os.getenv("RESEND_API_KEY", ""),
        email_from=os.getenv("EMAIL_FROM", ""),
        email_to=os.getenv("EMAIL_TO", "rami@gateco.ai"),
        meta_access_token=os.getenv("META_ACCESS_TOKEN", ""),
        meta_ad_account_id=os.getenv("META_AD_ACCOUNT_ID", "1011149454836521"),
        meta_ig_account_id=os.getenv("META_IG_ACCOUNT_ID", ""),
        meta_api_version=os.getenv("META_API_VERSION", "v23.0"),
        whatsapp_provider=os.getenv("WHATSAPP_PROVIDER", "mock"),
        whatsapp_events_path=(
            Path(os.getenv("WHATSAPP_EVENTS_PATH") or os.getenv("WHATSAPP_BOT_EVENTS_PATH", ""))
            if os.getenv("WHATSAPP_EVENTS_PATH") or os.getenv("WHATSAPP_BOT_EVENTS_PATH")
            else None
        ),
        whatsapp_webhook_url=os.getenv("WHATSAPP_WEBHOOK_URL", ""),
        social_publishing_enabled=os.getenv("SOCIAL_PUBLISHING_ENABLED", "false").lower() == "true",
        buffer_access_token=os.getenv("BUFFER_ACCESS_TOKEN", ""),
        buffer_profile_id=os.getenv("BUFFER_PROFILE_ID", ""),
        execution_dry_run=os.getenv("EXECUTION_DRY_RUN", "true").lower() == "true",
        meta_execution_enabled=os.getenv("META_EXECUTION_ENABLED", "false").lower() == "true",
    )


def load_company_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Company config not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    if not isinstance(data, dict):
        raise ValueError(f"Company config must be a YAML object: {path}")

    return data


def load_objectives_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Objectives config not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    if not isinstance(data, dict):
        raise ValueError(f"Objectives config must be a YAML object: {path}")

    return data


def load_funnel_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Funnel config not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    if not isinstance(data, dict):
        raise ValueError(f"Funnel config must be a YAML object: {path}")

    return data


def load_company_knowledge(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Company knowledge file not found: {path}")

    return path.read_text(encoding="utf-8").strip()


def load_ceo_constitution(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"CEO constitution file not found: {path}")

    return path.read_text(encoding="utf-8").strip()


def load_hebrew_style_guide(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Hebrew style guide file not found: {path}")

    return path.read_text(encoding="utf-8").strip()
