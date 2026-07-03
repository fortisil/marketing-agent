from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
import json
from pathlib import Path
from typing import Any, Callable, Optional
from urllib.request import urlopen
from zoneinfo import ZoneInfo

from src.providers.base import MetricSnapshot


SUPPORTED_EVENTS = {
    "conversation_started",
    "qualified_lead",
    "demo_requested",
    "demo_booked",
    "proposal_sent",
    "customer",
    "human_handoff",
    "not_qualified",
}


class WhatsAppBotProvider:
    name = "whatsapp_bot"

    def __init__(
        self,
        provider: str = "mock",
        events_path: Optional[Path] = None,
        webhook_url: str = "",
        funnel_config: Optional[dict[str, Any]] = None,
        timezone: str = "Asia/Jerusalem",
        urlopen_func: Callable[..., Any] = urlopen,
    ) -> None:
        self.provider = (provider or "mock").strip().lower()
        self.events_path = events_path
        self.webhook_url = webhook_url
        self.funnel_config = funnel_config or {}
        self.timezone = timezone
        self.urlopen_func = urlopen_func

    def collect(self) -> MetricSnapshot:
        collected_at = datetime.now(ZoneInfo(self.timezone))

        try:
            events = self._collect_events(collected_at)
            metrics = self._summarize(events, collected_at)
        except Exception as exc:  # noqa: BLE001 - provider must never break the morning brief.
            return MetricSnapshot(
                provider=self.name,
                collected_at=collected_at,
                metrics={
                    "whatsapp_bot": self._unavailable(
                        f"WhatsApp bot provider failed: {exc.__class__.__name__}: {exc}"
                    )
                },
                notes=[f"WhatsApp bot provider failed in {self.provider} mode."],
            )

        return MetricSnapshot(
            provider=self.name,
            collected_at=collected_at,
            metrics={"whatsapp_bot": metrics},
            notes=[f"Collected WhatsApp bot funnel metrics in {self.provider} mode."],
        )

    def _collect_events(self, collected_at: datetime) -> list[dict[str, Any]]:
        if self.provider == "mock":
            return self._mock_events(collected_at)

        if self.provider == "json_events":
            if not self.events_path:
                raise ValueError("WHATSAPP_EVENTS_PATH is not configured.")
            if not self.events_path.exists():
                raise FileNotFoundError(f"WhatsApp events file not found: {self.events_path}")
            return self._load_events(self.events_path.read_text(encoding="utf-8"))

        if self.provider == "webhook":
            if not self.webhook_url:
                raise ValueError("WHATSAPP_WEBHOOK_URL is not configured.")
            with self.urlopen_func(self.webhook_url, timeout=15) as response:
                raw = response.read().decode("utf-8")
            return self._load_events(raw)

        raise ValueError(f"Unsupported WHATSAPP_PROVIDER: {self.provider}")

    def _load_events(self, raw: str) -> list[dict[str, Any]]:
        stripped = raw.strip()
        if not stripped:
            return []

        if stripped.startswith("["):
            data = json.loads(stripped)
            if not isinstance(data, list):
                raise ValueError("WhatsApp events JSON must be an array.")
            return [event for event in data if isinstance(event, dict)]

        events = []
        for line in stripped.splitlines():
            if not line.strip():
                continue
            event = json.loads(line)
            if isinstance(event, dict):
                events.append(event)
        return events

    def _summarize(self, events: list[dict[str, Any]], collected_at: datetime) -> dict[str, Any]:
        normalized_events = [self._normalize_event(event) for event in events]
        valid_events = [event for event in normalized_events if event.get("event") in SUPPORTED_EVENTS]
        today = collected_at.date()
        seven_days_ago = today - timedelta(days=6)

        today_events = [event for event in valid_events if self._event_date(event) == today]
        last_7_events = [
            event for event in valid_events if seven_days_ago <= self._event_date(event) <= today
        ]

        today_summary = self._window_summary(today_events)
        last_7_summary = self._window_summary(last_7_events)

        return {
            "available": True,
            "provider": self.provider,
            "source": self._source_label(),
            "primary_kpi": self.funnel_config.get("primary_kpi", "booked_demos"),
            "stages": self.funnel_config.get(
                "stages",
                [
                    "conversation_started",
                    "qualified_lead",
                    "demo_requested",
                    "demo_booked",
                    "proposal_sent",
                    "customer",
                ],
            ),
            "events_path": str(self.events_path) if self.events_path else "",
            "webhook_url_configured": bool(self.webhook_url),
            "total_events_loaded": len(valid_events),
            "today": today_summary,
            "last_7_days": last_7_summary,
            "funnel_health_score": today_summary["funnel_health_score"],
            "today_bottleneck": today_summary["bottleneck"],
            "highest_impact_recommendation": self._recommendation_for_bottleneck(
                today_summary["bottleneck"]
            ),
        }

    def _window_summary(self, events: list[dict[str, Any]]) -> dict[str, Any]:
        counts = self._funnel_counts(events)
        rates = self._conversion_rates(counts)
        average_response_time = self._average_response_time(events)
        health_score = self._funnel_health_score(counts, rates)
        bottleneck = self._bottleneck(counts, rates)
        return {
            **counts,
            "conversion_rates": rates,
            "average_response_time_seconds": average_response_time,
            "funnel_health_score": health_score,
            "bottleneck": bottleneck,
        }

    def _funnel_counts(self, events: list[dict[str, Any]]) -> dict[str, int]:
        conversations_by_event: dict[str, set[str]] = defaultdict(set)

        for event in events:
            conversation_id = str(event.get("conversation_id") or "")
            if not conversation_id:
                continue
            conversations_by_event[str(event["event"])].add(conversation_id)

        demo_bookings = len(conversations_by_event["demo_booked"])
        customers = len(conversations_by_event["customer"])
        return {
            "conversations": len(conversations_by_event["conversation_started"]),
            "qualified_leads": len(conversations_by_event["qualified_lead"]),
            "demo_requests": len(conversations_by_event["demo_requested"]),
            "demo_bookings": demo_bookings,
            "demos_booked": demo_bookings,
            "proposals_sent": len(conversations_by_event["proposal_sent"]),
            "customers": customers,
            "human_handoffs": len(conversations_by_event["human_handoff"]),
            "not_qualified": len(conversations_by_event["not_qualified"]),
        }

    def _conversion_rates(self, counts: dict[str, int]) -> dict[str, float]:
        conversations = counts["conversations"]
        qualified = counts["qualified_leads"]
        demos = counts["demo_bookings"]
        customers = counts["customers"]
        qualified_to_demo = self._rate(demos, qualified)
        conversation_to_demo = self._rate(demos, conversations)
        return {
            "conversation_to_qualified": self._rate(qualified, conversations),
            "qualified_to_demo": qualified_to_demo,
            "qualified_to_demo_booked": qualified_to_demo,
            "demo_to_customer": self._rate(customers, demos),
            "conversation_to_customer": self._rate(customers, conversations),
            "conversation_to_demo_booked": conversation_to_demo,
        }

    def _funnel_health_score(self, counts: dict[str, int], rates: dict[str, float]) -> int:
        volume_score = min(counts["conversations"] / 10, 1.0) * 25
        qualification_score = rates["conversation_to_qualified"] * 25
        demo_score = rates["qualified_to_demo"] * 30
        customer_score = rates["demo_to_customer"] * 20
        return int(round(volume_score + qualification_score + demo_score + customer_score))

    def _bottleneck(self, counts: dict[str, int], rates: dict[str, float]) -> str:
        if counts["conversations"] < 5:
            return "low_conversation_volume"
        if rates["conversation_to_qualified"] < 0.3:
            return "qualification"
        if rates["qualified_to_demo"] < 0.4:
            return "demo_scheduling"
        if counts["demo_bookings"] >= 3 and rates["demo_to_customer"] < 0.2:
            return "demo_to_customer"
        return "healthy_or_learning"

    def _recommendation_for_bottleneck(self, bottleneck: str) -> str:
        recommendations = {
            "low_conversation_volume": "Improve Instagram, website, and ads CTAs into WhatsApp.",
            "qualification": "Improve the bot opening questions and qualification logic.",
            "demo_scheduling": "Improve the scheduling CTA and reduce booking friction.",
            "demo_to_customer": "Review demo quality, follow-up timing, and proposal handling.",
            "healthy_or_learning": "Keep optimizing the WhatsApp demo-booking flow.",
        }
        return recommendations.get(bottleneck, recommendations["healthy_or_learning"])

    def _average_response_time(self, events: list[dict[str, Any]]) -> Optional[float]:
        response_times = []
        for event in events:
            metadata = event.get("metadata") if isinstance(event.get("metadata"), dict) else {}
            value = metadata.get("response_time_seconds")
            if value is None and metadata.get("bot_response_ms") is not None:
                value = float(metadata["bot_response_ms"]) / 1000
            if value is None:
                continue
            try:
                response_times.append(float(value))
            except (TypeError, ValueError):
                continue
        if not response_times:
            return None
        return round(sum(response_times) / len(response_times), 2)

    def _normalize_event(self, event: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(event)
        normalized["event"] = str(event.get("event") or event.get("event_type") or "")
        return normalized

    def _event_date(self, event: dict[str, Any]):
        timestamp = str(event.get("timestamp") or "")
        if not timestamp:
            return datetime.min.date()
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=ZoneInfo(self.timezone))
        return parsed.astimezone(ZoneInfo(self.timezone)).date()

    def _rate(self, numerator: int, denominator: int) -> float:
        if denominator <= 0:
            return 0.0
        return round(numerator / denominator, 4)

    def _source_label(self) -> str:
        if self.provider == "json_events":
            return "json_events"
        if self.provider == "webhook":
            return "webhook"
        return "mock"

    def _mock_events(self, collected_at: datetime) -> list[dict[str, Any]]:
        today = collected_at.date().isoformat()
        yesterday = (collected_at.date() - timedelta(days=1)).isoformat()
        base = [
            (today, "conv_001", "conversation_started"),
            (today, "conv_001", "qualified_lead"),
            (today, "conv_001", "demo_requested"),
            (today, "conv_001", "demo_booked"),
            (today, "conv_002", "conversation_started"),
            (today, "conv_002", "qualified_lead"),
            (today, "conv_003", "conversation_started"),
            (today, "conv_003", "human_handoff"),
            (today, "conv_004", "conversation_started"),
            (yesterday, "conv_005", "conversation_started"),
            (yesterday, "conv_005", "qualified_lead"),
            (yesterday, "conv_005", "demo_requested"),
            (yesterday, "conv_005", "demo_booked"),
            (yesterday, "conv_005", "proposal_sent"),
        ]
        events = []
        for event_date, conversation_id, event_name in base:
            events.append(
                {
                    "timestamp": f"{event_date}T09:00:00+03:00",
                    "conversation_id": conversation_id,
                    "phone_hash": f"mock_{conversation_id}",
                    "event": event_name,
                    "metadata": {"response_time_seconds": 4} if event_name == "conversation_started" else {},
                }
            )
        return events

    def _unavailable(self, reason: str) -> dict[str, Any]:
        return {
            "available": False,
            "provider": self.provider,
            "reason": reason,
            "primary_kpi": self.funnel_config.get("primary_kpi", "booked_demos"),
            "today": {},
            "last_7_days": {},
        }
