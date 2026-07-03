from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from src.providers.base import MetricSnapshot


class MetaMcpProvider:
    name = "meta_mcp"

    def __init__(
        self,
        ad_account_id: str,
        instagram_username: str,
        timezone: str,
    ) -> None:
        self.ad_account_id = ad_account_id
        self.instagram_username = instagram_username
        self.timezone = timezone

    def collect(self) -> MetricSnapshot:
        instructions = [
            "Call Meta MCP ads_get_ad_accounts",
            f"Call Meta MCP ads_get_ig_accounts for ad account {self.ad_account_id}",
            f"Call Meta MCP ads_get_ig_media for {self.instagram_username} if available",
            "Call Meta MCP ads_get_ad_entities for campaign/ad performance",
        ]
        payload: dict[str, Any] = {
            "available": False,
            "provider": self.name,
            "ad_account_id": self.ad_account_id,
            "instagram_username": self.instagram_username,
            "requires_external_mcp_execution": True,
            "instructions": instructions,
        }
        return MetricSnapshot(
            provider=self.name,
            collected_at=datetime.now(ZoneInfo(self.timezone)),
            metrics={"marketing_platform_mcp": payload},
            notes=["Meta MCP is the preferred execution layer, but this local run cannot invoke MCP tools."],
        )
