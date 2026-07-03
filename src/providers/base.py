from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol


@dataclass(frozen=True)
class MetricSnapshot:
    provider: str
    collected_at: datetime
    metrics: dict[str, Any]
    notes: list[str] = field(default_factory=list)


class MetricsProvider(Protocol):
    name: str

    def collect(self) -> MetricSnapshot:
        """Collect one normalized metric snapshot from a marketing data source."""
