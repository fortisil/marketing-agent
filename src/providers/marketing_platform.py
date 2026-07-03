from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from zoneinfo import ZoneInfo

from src.providers.base import MetricSnapshot
from src.providers.meta_graph import MetaGraphProvider, UrlOpen
from src.providers.meta_mcp import MetaMcpProvider


class MarketingPlatformProvider:
    name = "marketing_platform"

    def __init__(
        self,
        company_config: dict[str, Any],
        access_token: str,
        env_ad_account_id: str,
        ig_account_id: str,
        api_version: str,
        timezone: str,
        urlopen: Optional[UrlOpen] = None,
    ) -> None:
        self.company_config = company_config
        self.access_token = access_token
        self.env_ad_account_id = env_ad_account_id
        self.ig_account_id = ig_account_id
        self.api_version = api_version
        self.timezone = timezone
        self.urlopen = urlopen

    def collect(self) -> MetricSnapshot:
        config = self.company_config.get("marketing_platform", {})
        provider = config.get("provider", "meta_mcp")
        fallback_provider = config.get("fallback_provider", "meta_graph")
        ad_account_id = str(config.get("meta_ad_account_id") or self.env_ad_account_id)
        instagram_username = str(config.get("instagram_username") or "")

        if provider == "meta_graph":
            graph_snapshot = self._collect_graph(ad_account_id)
            return self._snapshot(provider, fallback_provider, graph_snapshot, None)

        if provider == "meta_mcp":
            mcp_snapshot = MetaMcpProvider(
                ad_account_id=ad_account_id,
                instagram_username=instagram_username,
                timezone=self.timezone,
            ).collect()
            graph_snapshot = None
            if fallback_provider == "meta_graph" and self.access_token:
                graph_snapshot = self._collect_graph(ad_account_id)
            return self._snapshot(provider, fallback_provider, graph_snapshot, mcp_snapshot)

        fallback_snapshot = None
        if fallback_provider == "meta_graph":
            fallback_snapshot = self._collect_graph(ad_account_id)
        return self._snapshot(provider, fallback_provider, fallback_snapshot, None)

    def _collect_graph(self, ad_account_id: str) -> MetricSnapshot:
        return MetaGraphProvider(
            access_token=self.access_token,
            ad_account_id=ad_account_id,
            ig_account_id=self.ig_account_id,
            api_version=self.api_version,
            timezone=self.timezone,
            urlopen=self.urlopen,
        ).collect()

    def _snapshot(
        self,
        provider: str,
        fallback_provider: str,
        graph_snapshot: Optional[MetricSnapshot],
        mcp_snapshot: Optional[MetricSnapshot],
    ) -> MetricSnapshot:
        mcp_payload = (mcp_snapshot.metrics.get("marketing_platform_mcp", {}) if mcp_snapshot else {})
        graph_payload = (graph_snapshot.metrics.get("meta_ads", {}) if graph_snapshot else {})
        graph_available = bool(graph_payload.get("available"))
        mcp_required = bool(mcp_payload.get("requires_external_mcp_execution"))
        metrics_available = graph_available

        graph_api_status = {
            "configured": bool(self.access_token),
            "available": graph_available,
            "reason": graph_payload.get("reason") if graph_payload else "Graph API fallback was not attempted.",
        }

        platform_payload = {
            "provider": provider,
            "fallback_provider": fallback_provider,
            "metrics_available": metrics_available,
            "mcp_required_actions": mcp_payload.get("instructions", []),
            "graph_api_status": graph_api_status,
            "mcp": mcp_payload,
            "meta_ads": graph_payload,
        }

        notes = []
        if mcp_required:
            notes.append("Meta MCP requires external execution by ChatGPT/orchestrator MCP tools.")
        if graph_snapshot:
            notes.extend(graph_snapshot.notes)
        if not notes:
            notes.append("Marketing platform provider returned no live metrics.")

        return MetricSnapshot(
            provider=self.name,
            collected_at=datetime.now(ZoneInfo(self.timezone)),
            metrics={
                "marketing_platform": platform_payload,
                "meta_ads": graph_payload or mcp_payload,
            },
            notes=notes,
        )
