from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from src.providers.base import MetricSnapshot


class MockMetricsProvider:
    name = "mock_marketing"

    def __init__(self, company_config: dict[str, Any], timezone: str) -> None:
        self.company_config = company_config
        self.timezone = timezone

    def collect(self) -> MetricSnapshot:
        return MetricSnapshot(
            provider=self.name,
            collected_at=datetime.now(ZoneInfo(self.timezone)),
            metrics=dict(self.company_config.get("mock_data", {})),
            notes=[
                "Temporary mock data until Instagram, WhatsApp Bot, Meta Ads, and Calendar providers are connected."
            ],
        )
