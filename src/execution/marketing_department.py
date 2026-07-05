from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from src.decisions.engine import DecisionContext


@dataclass(frozen=True)
class AgentSpec:
    name: str
    mission: str
    kpis: list[str]
    delegated_authority: dict[str, Any]
    retry: str
    memory: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "mission": self.mission,
            "kpis": self.kpis,
            "delegated_authority": self.delegated_authority,
            "retry": self.retry,
            "memory": self.memory,
        }


@dataclass(frozen=True)
class AgentOutput:
    agent: str
    status: str
    daily_output: dict[str, Any]
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "agent": self.agent,
            "status": self.status,
            "daily_output": self.daily_output,
        }
        if self.error:
            payload["error"] = self.error
        return payload


@dataclass(frozen=True)
class MarketingDepartmentOutput:
    department: str
    initiative: str
    mission: str
    status: str
    agents: list[AgentSpec]
    outputs: list[AgentOutput]
    action_log: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "department": self.department,
            "initiative": self.initiative,
            "mission": self.mission,
            "status": self.status,
            "agents": [agent.to_dict() for agent in self.agents],
            "outputs": [output.to_dict() for output in self.outputs],
            "action_log": self.action_log,
        }


class MarketingDepartment:
    """Autonomous Marketing Operations department."""

    department = "Marketing Operations"
    initiative = "Acquire the first three paying law firms"
    mission = "Generate one qualified law firm demo today."

    def __init__(
        self,
        *,
        company_config: dict[str, Any],
        objectives_config: dict[str, Any],
        timezone: str,
        social_publishing_enabled: bool = False,
        buffer_configured: bool = False,
        meta_execution_enabled: bool = False,
    ) -> None:
        self.company_config = company_config
        self.objectives_config = objectives_config
        self.timezone = timezone
        self.social_publishing_enabled = social_publishing_enabled
        self.buffer_configured = buffer_configured
        self.meta_execution_enabled = meta_execution_enabled

    def run(self, decision_context: DecisionContext) -> MarketingDepartmentOutput:
        now = datetime.now(ZoneInfo(self.timezone))
        marketing = self.company_config.get("marketing", {})
        cta = marketing.get("cta", {})
        summary = decision_context.summary
        whatsapp_bot = summary.get("whatsapp_bot", {})
        meta_ads = summary.get("meta_ads", {})
        website_intelligence = summary.get("website_intelligence", {})
        brand_intelligence = summary.get("brand_intelligence", {})

        agents = self._agents()
        outputs = [
            self._content_output(cta),
            self._design_output(brand_intelligence),
            self._video_output(cta),
            self._social_output(),
            self._ads_output(meta_ads),
            self._analytics_output(whatsapp_bot, meta_ads),
            self._website_output(website_intelligence, cta),
            self._outreach_output(cta),
        ]
        action_log = [
            self._action_record(now, decision_context.run_date, output)
            for output in outputs
        ]
        status = (
            "operating_with_external_execution"
            if self.social_publishing_enabled and self.buffer_configured and self.meta_execution_enabled
            else "operating_in_preparation_mode"
        )
        return MarketingDepartmentOutput(
            department=self.department,
            initiative=self.initiative,
            mission=self.mission,
            status=status,
            agents=agents,
            outputs=outputs,
            action_log=action_log,
        )

    def _agents(self) -> list[AgentSpec]:
        authority = self.objectives_config.get("delegated_authority", {})
        marketing = authority.get("marketing", {})
        ads = authority.get("ads", {})
        website = authority.get("website", {})
        sales = authority.get("sales", {})
        return [
            AgentSpec(
                "Content Agent",
                "Decide and prepare today's highest-impact content.",
                ["content_published", "qualified_demo_intent"],
                {
                    "create_posts": marketing.get("create_posts"),
                    "create_post_drafts": marketing.get("create_post_drafts"),
                    "publish_posts": marketing.get("publish_posts"),
                },
                "tomorrow 08:00",
                "memory/actions/YYYY-MM-DD.json",
            ),
            AgentSpec(
                "Design Agent",
                "Produce brand-safe creative specifications and assets.",
                ["brand_compliance", "creative_ready"],
                {"generate_images": marketing.get("generate_images")},
                "tomorrow 08:00",
                "memory/actions/YYYY-MM-DD.json",
            ),
            AgentSpec(
                "Video Agent",
                "Prepare short-form video scripts and production assets.",
                ["video_ready", "demo_cta_clarity"],
                {"generate_video_scripts": marketing.get("generate_video_scripts")},
                "tomorrow 08:00",
                "memory/actions/YYYY-MM-DD.json",
            ),
            AgentSpec(
                "Social Agent",
                "Publish or schedule approved content and record URLs.",
                ["posts_published", "post_urls_recorded"],
                {
                    "publish_posts": marketing.get("publish_posts"),
                    "publish_reels": marketing.get("publish_reels"),
                },
                "next run after executor is configured",
                "memory/actions/YYYY-MM-DD.json",
            ),
            AgentSpec(
                "Ads Agent",
                "Promote winning content within delegated budget.",
                ["campaign_status", "spend_within_budget", "demo_requests"],
                {
                    "create_campaigns": ads.get("create_campaigns"),
                    "pause_campaigns": ads.get("pause_campaigns"),
                    "daily_budget_limit_ils": ads.get("daily_budget_limit_ils"),
                },
                "tomorrow 08:00",
                "memory/actions/YYYY-MM-DD.json",
            ),
            AgentSpec(
                "Analytics Agent",
                "Measure business outcomes from content and campaigns.",
                ["verified_demo_requests", "verified_whatsapp_clicks", "campaign_ctr"],
                {},
                "tomorrow 08:00",
                "memory/actions/YYYY-MM-DD.json",
            ),
            AgentSpec(
                "Website Agent",
                "Find and prepare conversion improvements on owned pages.",
                ["cta_quality", "demo_conversion_rate"],
                {
                    "update_cta": website.get("update_cta"),
                    "update_copy": website.get("update_copy"),
                },
                "tomorrow 08:00",
                "memory/actions/YYYY-MM-DD.json",
            ),
            AgentSpec(
                "Outreach Agent",
                "Prepare ICP outreach that can create qualified demos.",
                ["qualified_prospects", "outreach_drafts_ready"],
                {
                    "follow_up": sales.get("follow_up"),
                    "send_proposal": sales.get("send_proposal"),
                },
                "tomorrow 08:00",
                "memory/actions/YYYY-MM-DD.json",
            ),
        ]

    def _content_output(self, cta: dict[str, Any]) -> AgentOutput:
        phone = cta.get("phone", "+972559720244")
        return AgentOutput(
            agent="Content Agent",
            status="prepared",
            daily_output={
                "publish": "Reel",
                "theme": "How AI saves Israeli law firms time before the first consultation.",
                "format_reason": "Short video is the best awareness format for a founder-led validation push.",
                "hebrew_copy": (
                    "עורכי דין מבזבזים שעות על תיאום, שאלות חוזרות וסינון פניות. "
                    "ChatBot2U עוזר להפוך פניות WhatsApp לשיחות מסודרות ודמואים כשירים."
                ),
                "english_internal_rationale": (
                    "Use a concrete time-saving angle to attract law firms that feel intake friction today."
                ),
                "cta": f"Book a demo on WhatsApp: {phone}",
                "posting_time": "10:00 Asia/Jerusalem",
                "tomorrow_queue": [
                    "Carousel: 5 intake mistakes law firms can automate",
                    "Story: poll about missed WhatsApp inquiries",
                ],
            },
        )

    def _design_output(self, brand_intelligence: dict[str, Any]) -> AgentOutput:
        return AgentOutput(
            agent="Design Agent",
            status="prepared" if brand_intelligence else "prepared_with_brand_defaults",
            daily_output={
                "asset_specs": ["Instagram Reel cover", "Story frame", "thumbnail"],
                "brand_source": "Brand Brain" if brand_intelligence else "configured brand defaults",
                "image_prompt": (
                    "Create a clean B2B SaaS visual for Israeli law firms: WhatsApp intake, legal desk, "
                    "clear CTA, ChatBot2U brand colors, no stock-photo feel."
                ),
                "guardrail": "Do not publish creative that conflicts with the approved logo or brand colors.",
            },
        )

    def _video_output(self, cta: dict[str, Any]) -> AgentOutput:
        return AgentOutput(
            agent="Video Agent",
            status="prepared",
            daily_output={
                "heygen_script": (
                    "Israeli law firms lose time answering the same intake questions. "
                    "ChatBot2U turns WhatsApp inquiries into structured qualified conversations. "
                    f"Book a demo today: {cta.get('phone', '+972559720244')}."
                ),
                "storyboard": [
                    "Problem: repeated intake messages",
                    "Solution: AI WhatsApp qualification",
                    "Outcome: one cleaner path to a booked demo",
                ],
                "voice_over": "Confident founder-led Hebrew, practical and direct.",
                "thumbnail": "Law firm intake before and after ChatBot2U.",
                "cta": "Book a WhatsApp demo.",
            },
        )

    def _social_output(self) -> AgentOutput:
        if not self.social_publishing_enabled or not self.buffer_configured:
            return AgentOutput(
                agent="Social Agent",
                status="blocked",
                daily_output={
                    "executed": False,
                    "reason": "Buffer publishing executor is not configured in this runtime.",
                    "required_provider": "Buffer",
                    "recorded_urls": [],
                    "recorded_post_ids": [],
                },
                error="waiting_for_buffer_execution_provider",
            )
        return AgentOutput(
            agent="Social Agent",
            status="prepared_for_external_executor",
            daily_output={
                "executed": False,
                "reason": "Publishing payload is ready; Buffer API execution is not implemented in this repository yet.",
                "required_provider": "Buffer",
                "recorded_urls": [],
                "recorded_post_ids": [],
            },
        )

    def _ads_output(self, meta_ads: dict[str, Any]) -> AgentOutput:
        verified_campaign = bool(meta_ads.get("verified") and meta_ads.get("campaign_status") == "active")
        if not self.meta_execution_enabled:
            return AgentOutput(
                agent="Ads Agent",
                status="blocked",
                daily_output={
                    "campaign_status": meta_ads.get("campaign_status", "unknown"),
                    "executed": False,
                    "reason": "Meta execution provider is not configured.",
                    "budget_rule": "Do not exceed ILS 20/day. No Saturday spend. Friday morning only.",
                    "verified_active_campaign": verified_campaign,
                },
                error="waiting_for_meta_execution_provider",
            )
        return AgentOutput(
            agent="Ads Agent",
            status="prepared_for_external_executor",
            daily_output={
                "campaign_status": meta_ads.get("campaign_status", "unknown"),
                "executed": False,
                "reason": "Campaign payload requires real Meta execution provider before it can be marked active.",
                "budget_rule": "Do not exceed ILS 20/day. No Saturday spend. Friday morning only.",
                "verified_active_campaign": verified_campaign,
            },
        )

    def _analytics_output(self, whatsapp_bot: dict[str, Any], meta_ads: dict[str, Any]) -> AgentOutput:
        verified = bool(whatsapp_bot.get("verified")) or bool(meta_ads.get("verified"))
        return AgentOutput(
            agent="Analytics Agent",
            status="collected" if verified else "blocked",
            daily_output={
                "organic_reach": None,
                "ctr": None,
                "whatsapp_clicks": None,
                "demo_requests": None,
                "campaign_performance": None,
                "learning": (
                    "At least one verified source is available for learning."
                    if verified
                    else "No verified acquisition outcome data available yet."
                ),
            },
            error=None if verified else "waiting_for_verified_marketing_data",
        )

    def _website_output(self, website_intelligence: dict[str, Any], cta: dict[str, Any]) -> AgentOutput:
        return AgentOutput(
            agent="Website Agent",
            status="prepared",
            daily_output={
                "reviewed": True,
                "weak_ctas": website_intelligence.get("missing_or_weak_ctas", []),
                "cta_patch_spec": {
                    "above_fold": f"Add WhatsApp demo CTA: {cta.get('phone', '+972559720244')}",
                    "after_first_section": "Add Book a Demo CTA with law-firm-specific proof point.",
                },
                "pull_request_created": False,
                "reason_pr_not_created": "No target website checkout path was available to patch in this runtime.",
            },
        )

    def _outreach_output(self, cta: dict[str, Any]) -> AgentOutput:
        return AgentOutput(
            agent="Outreach Agent",
            status="prepared",
            daily_output={
                "icp": "Israeli law firms with visible intake friction and active WhatsApp/contact forms.",
                "prospects_to_research": 10,
                "drafts_ready": [
                    {
                        "channel": "email_or_whatsapp_where_permitted",
                        "message": (
                            "Hi, I noticed your firm receives client inquiries through WhatsApp/contact forms. "
                            "ChatBot2U helps qualify those inquiries automatically and route serious cases to a demo. "
                            f"Open to a short walkthrough? {cta.get('phone', '+972559720244')}"
                        ),
                    }
                ],
                "sent": False,
                "reason_not_sent": "No verified outreach permission list or sending provider is configured.",
            },
        )

    def _action_record(self, now: datetime, run_date: str, output: AgentOutput) -> dict[str, Any]:
        status_map = {
            "collected": "executed",
            "prepared": "prepared",
            "prepared_with_brand_defaults": "prepared",
            "prepared_for_external_executor": "prepared",
            "blocked": "blocked",
        }
        return {
            "timestamp": now.isoformat(),
            "run_date": run_date,
            "initiative": self.initiative,
            "department": self.department,
            "agent": output.agent,
            "action": self._action_name(output),
            "expected_business_impact": (
                "High" if output.agent in {"Content Agent", "Website Agent", "Outreach Agent"} else "Medium"
            ),
            "delegated_authority_used": self._authority_for(output.agent),
            "status": status_map.get(output.status, output.status),
            "result": output.daily_output,
            "next_step": self._next_step(output),
            "retry": "tomorrow 08:00 Asia/Jerusalem" if output.status == "blocked" else None,
            "error": output.error,
        }

    def _action_name(self, output: AgentOutput) -> str:
        actions = {
            "Content Agent": "Prepared today's law-firm Reel content plan",
            "Design Agent": "Prepared brand-safe creative specifications",
            "Video Agent": "Prepared HeyGen video script and storyboard",
            "Social Agent": "Checked social publishing readiness",
            "Ads Agent": "Checked paid promotion readiness",
            "Analytics Agent": "Checked verified marketing outcome data",
            "Website Agent": "Prepared homepage CTA improvement spec",
            "Outreach Agent": "Prepared ICP outreach draft",
        }
        return actions.get(output.agent, f"Ran {output.agent}")

    def _authority_for(self, agent: str) -> str:
        authority = {
            "Content Agent": "marketing.create_posts / marketing.publish_posts",
            "Design Agent": "marketing.generate_images",
            "Video Agent": "marketing.generate_video_scripts",
            "Social Agent": "marketing.publish_posts / marketing.publish_reels",
            "Ads Agent": "ads.create_campaigns / ads.daily_budget_limit_ils",
            "Analytics Agent": "measurement only",
            "Website Agent": "website.update_cta / website.update_copy",
            "Outreach Agent": "sales.follow_up / sales.send_proposal",
        }
        return authority.get(agent, "unknown")

    def _next_step(self, output: AgentOutput) -> str:
        if output.agent == "Social Agent" and output.status == "blocked":
            return "Configure Buffer executor before marking any post as published."
        if output.agent == "Ads Agent" and output.status == "blocked":
            return "Configure real Meta execution provider before creating campaigns."
        if output.agent == "Analytics Agent" and output.status == "blocked":
            return "Connect WhatsApp events and Meta metrics before learning from outcomes."
        return "Use this output in today's execution queue."


def attach_marketing_department_output(
    decision_context: DecisionContext,
    output: MarketingDepartmentOutput,
) -> None:
    payload = output.to_dict()
    decision_context.summary["marketing_department"] = payload
    decision_context.summary["execution_departments"] = {
        "frozen_executive_layer": True,
        "active_department": "Marketing Operations",
        "department_status": output.status,
        "success_criterion": (
            "Operate for 14 days with more content published, more experiments run, "
            "a better website, a complete audit trail, and more qualified demos."
        ),
    }
    executed = [
        action["action"]
        for action in output.action_log
        if action.get("status") == "executed"
    ]
    prepared = [
        action["action"]
        for action in output.action_log
        if action.get("status") == "prepared"
    ]
    blocked = [
        action["action"]
        for action in output.action_log
        if action.get("status") == "blocked"
    ]
    decision_context.summary["executed_actions_today"] = executed or ["none"]
    decision_context.summary["prepared_actions"] = prepared
    decision_context.summary["blocked_actions"] = blocked
    decision_context.daily_report.autonomous_action_log.extend(output.action_log)
