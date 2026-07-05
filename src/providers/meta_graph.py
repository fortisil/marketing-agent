from __future__ import annotations

from datetime import date, datetime, timedelta
import json
import urllib.parse
import urllib.request
from typing import Any, Callable, Optional
from zoneinfo import ZoneInfo

from src.providers.base import MetricSnapshot


UrlOpen = Callable[[str], Any]


class MetaGraphProvider:
    name = "meta_graph"

    def __init__(
        self,
        access_token: str,
        ad_account_id: str,
        ig_account_id: str,
        api_version: str,
        timezone: str,
        urlopen: Optional[UrlOpen] = None,
    ) -> None:
        self.access_token = access_token
        self.ad_account_id = ad_account_id
        self.ig_account_id = ig_account_id
        self.api_version = api_version
        self.timezone = timezone
        self.urlopen = urlopen or urllib.request.urlopen

    def collect(self) -> MetricSnapshot:
        collected_at = datetime.now(ZoneInfo(self.timezone))

        if not self.access_token:
            return MetricSnapshot(
                provider=self.name,
                collected_at=collected_at,
                metrics={
                    "meta_ads": self._unavailable(
                        "META_ACCESS_TOKEN is not configured.",
                        ad_account_id=self.ad_account_id,
                    )
                },
                notes=["Meta Graph API fallback credentials missing; real campaign metrics unavailable."],
            )

        if not self.ad_account_id:
            return MetricSnapshot(
                provider=self.name,
                collected_at=collected_at,
                metrics={"meta_ads": self._unavailable("META_AD_ACCOUNT_ID is not configured.")},
                notes=["Meta ad account id missing; real campaign metrics unavailable."],
            )

        try:
            metrics = self._collect_meta_metrics()
        except Exception as exc:  # noqa: BLE001 - provider must never crash daily brief generation.
            metrics = {
                "meta_ads": self._unavailable(
                    f"Meta Graph API request failed: {exc.__class__.__name__}",
                    ad_account_id=self.ad_account_id,
                )
            }
            return MetricSnapshot(
                provider=self.name,
                collected_at=collected_at,
                metrics=metrics,
                notes=["Meta Graph API unavailable or permissions failed; using structured unavailable status."],
            )

        return MetricSnapshot(
            provider=self.name,
            collected_at=collected_at,
            metrics=metrics,
            notes=["Collected Meta Graph API metrics; Instagram metrics included when configured and permitted."],
        )

    def _collect_meta_metrics(self) -> dict[str, Any]:
        today = date.today().isoformat()
        last_7_start = (date.today() - timedelta(days=6)).isoformat()
        account_node = self._ad_account_node()

        account = self._get(
            account_node,
            {
                "fields": "id,name,account_status,currency,timezone_name,amount_spent,balance",
            },
        )
        campaigns = self._get(
            f"{account_node}/campaigns",
            {
                "fields": "id,name,status,effective_status,objective,created_time,updated_time",
                "limit": "50",
            },
        )
        adsets = self._get(
            f"{account_node}/adsets",
            {
                "fields": "id,name,status,effective_status,campaign_id,daily_budget,lifetime_budget",
                "limit": "50",
            },
        )
        ads = self._get(
            f"{account_node}/ads",
            {
                "fields": "id,name,status,effective_status,campaign_id,adset_id",
                "limit": "50",
            },
        )
        today_insights = self._insights(account_node, today, today)
        last_7_insights = self._insights(account_node, last_7_start, today)
        delivery_errors = self._delivery_errors(campaigns, adsets, ads)
        instagram = self._instagram_metrics()

        return {
            "meta_ads": {
                "available": True,
                "provider": self.name,
                "source": "meta_graph",
                "verified": True,
                "ad_account_id": self.ad_account_id,
                "account": account,
                "campaigns_summary": self._entity_summary(campaigns.get("data", [])),
                "adsets_summary": self._entity_summary(adsets.get("data", [])),
                "ads_summary": self._entity_summary(ads.get("data", [])),
                "today": self._summarize_insights(today_insights),
                "last_7_days": self._summarize_insights(last_7_insights),
                "delivery_errors": delivery_errors,
                "instagram": instagram,
                "campaign_status": self._campaign_status(campaigns.get("data", [])),
                "metric_sources": [
                    {
                        "metric": "meta_spend_today",
                        "value": self._summarize_insights(today_insights)["spend"],
                        "source": "meta_graph",
                        "verified": True,
                    },
                    {
                        "metric": "meta_campaign_status",
                        "value": self._campaign_status(campaigns.get("data", [])),
                        "source": "meta_graph",
                        "verified": True,
                    },
                ],
            }
        }

    def _insights(self, node: str, since: str, until: str) -> dict[str, Any]:
        return self._get(
            f"{node}/insights",
            {
                "fields": "spend,impressions,reach,clicks,ctr,cost_per_result,actions",
                "time_range": json.dumps({"since": since, "until": until}),
            },
        )

    def _instagram_metrics(self) -> dict[str, Any]:
        if not self.ig_account_id:
            return {
                "available": False,
                "reason": "META_IG_ACCOUNT_ID is not configured.",
                "recent_media": [],
            }

        try:
            media = self._get(
                f"{self.ig_account_id}/media",
                {
                    "fields": "id,caption,permalink,media_type,timestamp,comments_count,like_count",
                    "limit": "10",
                },
            )
        except Exception as exc:  # noqa: BLE001
            return {
                "available": False,
                "reason": f"Instagram media unavailable: {exc.__class__.__name__}",
                "recent_media": [],
            }

        recent_media = []
        for item in media.get("data", []):
            media_record = dict(item)
            media_record["insights"] = self._media_insights(item.get("id", ""))
            recent_media.append(media_record)

        return {
            "available": True,
            "ig_account_id": self.ig_account_id,
            "recent_media": recent_media,
        }

    def _media_insights(self, media_id: str) -> dict[str, Any]:
        if not media_id:
            return {"available": False, "reason": "Missing media id."}

        try:
            return self._get(
                f"{media_id}/insights",
                {"metric": "impressions,reach,saved,shares,comments,likes"},
            )
        except Exception as exc:  # noqa: BLE001
            return {"available": False, "reason": f"Media insights unavailable: {exc.__class__.__name__}"}

    def _get(self, path: str, params: dict[str, str]) -> dict[str, Any]:
        query = dict(params)
        query["access_token"] = self.access_token
        url = (
            f"https://graph.facebook.com/{self.api_version}/{path}"
            f"?{urllib.parse.urlencode(query)}"
        )

        with self.urlopen(url) as response:
            payload = response.read().decode("utf-8")

        data = json.loads(payload)
        if "error" in data:
            message = data["error"].get("message", "Meta API error")
            raise RuntimeError(message)
        return data

    def _ad_account_node(self) -> str:
        account_id = self.ad_account_id
        if account_id.startswith("act_"):
            return account_id
        return f"act_{account_id}"

    def _summarize_insights(self, insights: dict[str, Any]) -> dict[str, Any]:
        rows = insights.get("data", [])
        if not rows:
            return {
                "spend": 0.0,
                "impressions": 0,
                "reach": 0,
                "clicks": 0,
                "ctr": 0.0,
                "cost_per_result": None,
                "actions": [],
            }

        summary = {
            "spend": 0.0,
            "impressions": 0,
            "reach": 0,
            "clicks": 0,
            "ctr": 0.0,
            "cost_per_result": None,
            "actions": [],
        }
        ctr_values = []
        for row in rows:
            summary["spend"] += self._float(row.get("spend"))
            summary["impressions"] += self._int(row.get("impressions"))
            summary["reach"] += self._int(row.get("reach"))
            summary["clicks"] += self._int(row.get("clicks"))
            if row.get("ctr") is not None:
                ctr_values.append(self._float(row.get("ctr")))
            if row.get("cost_per_result") is not None:
                summary["cost_per_result"] = row.get("cost_per_result")
            summary["actions"].extend(row.get("actions", []))

        if ctr_values:
            summary["ctr"] = round(sum(ctr_values) / len(ctr_values), 4)
        summary["spend"] = round(summary["spend"], 2)
        return summary

    def _entity_summary(self, entities: list[dict[str, Any]]) -> dict[str, Any]:
        active = []
        paused = []
        other = []

        for entity in entities:
            status = str(entity.get("effective_status") or entity.get("status") or "").upper()
            record = {
                "id": entity.get("id"),
                "name": entity.get("name"),
                "status": entity.get("status"),
                "effective_status": entity.get("effective_status"),
            }
            if status == "ACTIVE":
                active.append(record)
            elif status == "PAUSED":
                paused.append(record)
            else:
                other.append(record)

        return {
            "total": len(entities),
            "active": active,
            "paused": paused,
            "other": other,
        }

    def _delivery_errors(
        self,
        campaigns: dict[str, Any],
        adsets: dict[str, Any],
        ads: dict[str, Any],
    ) -> list[str]:
        errors = []
        for label, response in (("campaigns", campaigns), ("adsets", adsets), ("ads", ads)):
            if "error" in response:
                errors.append(f"{label}: {response['error'].get('message', 'unknown error')}")
        return errors

    def _campaign_status(self, campaigns: list[dict[str, Any]]) -> str:
        if not campaigns:
            return "not_started"
        statuses = {
            str(campaign.get("effective_status") or campaign.get("status") or "").upper()
            for campaign in campaigns
        }
        if "ACTIVE" in statuses:
            return "active"
        if statuses and statuses <= {"PAUSED"}:
            return "paused"
        return "unknown"

    def _unavailable(self, reason: str, ad_account_id: str = "") -> dict[str, Any]:
        return {
            "available": False,
            "provider": self.name,
            "reason": reason,
            "ad_account_id": ad_account_id,
            "source": "unavailable",
            "verified": False,
            "campaign_status": "unknown",
            "campaign_status_note": "No campaign has been verified as active.",
            "metric_sources": [
                {
                    "metric": "meta_spend_today",
                    "value": None,
                    "source": "unavailable",
                    "verified": False,
                },
                {
                    "metric": "meta_campaign_status",
                    "value": "unknown",
                    "source": "unavailable",
                    "verified": False,
                },
            ],
            "instagram": {
                "available": False,
                "reason": "Meta Graph API fallback unavailable.",
                "recent_media": [],
            },
        }

    def _int(self, value: Any) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    def _float(self, value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
