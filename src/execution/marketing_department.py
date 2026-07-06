from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from src.decisions.engine import DecisionContext
from src.execution.connectors import (
    BufferExecutor,
    ExecutionResult,
    ExecutionTask,
    ImageExecutor,
)
from src.workforce import TaskPriority, WorkforceRuntime, WorkTask, Worker


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
    aeos_spec: dict[str, Any] = field(default_factory=dict)
    organization: dict[str, Any] = field(default_factory=dict)
    creative_brief: dict[str, Any] = field(default_factory=dict)
    campaign_lifecycle: dict[str, Any] = field(default_factory=dict)
    budget_status: dict[str, Any] = field(default_factory=dict)
    content_intelligence: dict[str, Any] = field(default_factory=dict)
    hypothesis_register: list[dict[str, Any]] = field(default_factory=list)
    decision_ledger: list[dict[str, Any]] = field(default_factory=list)
    business_memory: list[dict[str, Any]] = field(default_factory=list)
    execution_results: list[ExecutionResult] = field(default_factory=list)
    workforce: dict[str, Any] = field(default_factory=dict)
    action_log: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "department": self.department,
            "initiative": self.initiative,
            "mission": self.mission,
            "status": self.status,
            "agents": [agent.to_dict() for agent in self.agents],
            "outputs": [output.to_dict() for output in self.outputs],
            "aeos_spec": self.aeos_spec,
            "organization": self.organization,
            "creative_brief": self.creative_brief,
            "campaign_lifecycle": self.campaign_lifecycle,
            "budget_status": self.budget_status,
            "content_intelligence": self.content_intelligence,
            "hypothesis_register": self.hypothesis_register,
            "decision_ledger": self.decision_ledger,
            "business_memory": self.business_memory,
            "execution_results": [result.to_dict() for result in self.execution_results],
            "workforce": self.workforce,
            "action_log": self.action_log,
        }


class MarketingDepartment:
    """Autonomous Marketing Operations department."""

    department = "Marketing Operations"
    initiative = "Acquire the first three paying law firms"
    mission = "Generate one additional paying customer."

    def __init__(
        self,
        *,
        company_config: dict[str, Any],
        objectives_config: dict[str, Any],
        timezone: str,
        social_publishing_enabled: bool = False,
        buffer_access_token: str = "",
        buffer_profile_id: str = "",
        execution_dry_run: bool = True,
        image_generation_enabled: bool = False,
        openai_api_key: str = "",
        openai_image_model: str = "gpt-image-1",
        assets_root: Path | None = None,
        asset_public_base_url: str = "",
        asset_upload_provider: str = "",
        cloudinary_cloud_name: str = "",
        cloudinary_api_key: str = "",
        cloudinary_api_secret: str = "",
        memory_root: Path | None = None,
        meta_execution_enabled: bool = False,
    ) -> None:
        self.company_config = company_config
        self.objectives_config = objectives_config
        self.timezone = timezone
        self.social_publishing_enabled = social_publishing_enabled
        self.buffer_access_token = buffer_access_token
        self.buffer_profile_id = buffer_profile_id
        self.execution_dry_run = execution_dry_run
        self.image_generation_enabled = image_generation_enabled
        self.openai_api_key = openai_api_key
        self.openai_image_model = openai_image_model
        self.assets_root = assets_root or Path("assets/companies/chatbot2u")
        self.asset_public_base_url = asset_public_base_url.rstrip("/")
        self.asset_upload_provider = asset_upload_provider
        self.cloudinary_cloud_name = cloudinary_cloud_name
        self.cloudinary_api_key = cloudinary_api_key
        self.cloudinary_api_secret = cloudinary_api_secret
        self.memory_root = memory_root or Path("memory")
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
        creative_brief = self._creative_brief(cta, brand_intelligence, whatsapp_bot, meta_ads)
        content_output = self._content_output(cta, brand_intelligence, creative_brief)
        image_task = self._image_task(brand_intelligence, content_output, decision_context.run_date)
        image_workforce_result = self._run_workforce([image_task])
        image_result = self._result_for(image_workforce_result.execution_results, "ImageExecutor")
        buffer_task = self._buffer_task(
            content_output,
            image_result=image_result,
            run_date=decision_context.run_date,
        )
        social_workforce_result = (
            self._run_workforce([buffer_task])
            if image_result is not None and image_result.status == "completed"
            else None
        )
        execution_results = image_workforce_result.execution_results + (
            social_workforce_result.execution_results if social_workforce_result else []
        )
        buffer_result = self._result_for(execution_results, "BufferExecutor")
        design_output = self._design_output(
            brand_intelligence,
            image_task,
            image_result,
        )
        budget_status = self._budget_status(meta_ads)
        content_intelligence = self._content_intelligence(whatsapp_bot, meta_ads, buffer_result)
        social_output = self._social_output(
            content_output,
            image_result,
            buffer_result,
            decision_context.run_date,
        )
        outputs = [
            content_output,
            design_output,
            self._video_output(cta, brand_intelligence),
            social_output,
            self._ads_output(meta_ads, budget_status, content_intelligence),
            self._analytics_output(whatsapp_bot, meta_ads, content_intelligence),
            self._website_output(website_intelligence, cta),
            self._outreach_output(cta),
        ]
        action_log = [
            self._action_record(now, decision_context.run_date, output)
            for output in outputs
        ]
        status = (
            "operating_with_external_execution"
            if self.social_publishing_enabled
            and self.buffer_access_token
            and self.buffer_profile_id
            and not self.execution_dry_run
            and self.meta_execution_enabled
            else "operating_in_preparation_mode"
        )
        return MarketingDepartmentOutput(
            department=self.department,
            initiative=self.initiative,
            mission=self.mission,
            status=status,
            agents=agents,
            outputs=outputs,
            aeos_spec=self._aeos_spec(),
            organization=self._organization(),
            creative_brief=creative_brief,
            campaign_lifecycle=self._campaign_lifecycle(execution_results, content_intelligence),
            budget_status=budget_status,
            content_intelligence=content_intelligence,
            hypothesis_register=self._hypothesis_register(content_intelligence),
            decision_ledger=self._decision_ledger(content_output, creative_brief, content_intelligence),
            business_memory=self._business_memory(content_intelligence),
            execution_results=execution_results,
            workforce={
                "workers": [
                    worker.to_dict()
                    for worker in (
                        social_workforce_result.workers if social_workforce_result else image_workforce_result.workers
                    )
                ],
                "tasks": [
                    task.to_dict()
                    for task in (
                        social_workforce_result.tasks if social_workforce_result else image_workforce_result.tasks
                    )
                ],
                "escalations": image_workforce_result.escalations
                + (social_workforce_result.escalations if social_workforce_result else []),
            },
            action_log=action_log,
        )

    def _run_workforce(self, tasks: list[WorkTask]):
        runtime = WorkforceRuntime(
            memory_root=self.memory_root,
            timezone=self.timezone,
            workers=self._workers(),
            connectors=[
                ImageExecutor(
                    api_key=self.openai_api_key,
                    assets_root=self.assets_root,
                    timezone=self.timezone,
                    enabled=self.image_generation_enabled,
                    dry_run=self.execution_dry_run,
                    model=self.openai_image_model,
                    upload_provider=self.asset_upload_provider,
                    cloudinary_cloud_name=self.cloudinary_cloud_name,
                    cloudinary_api_key=self.cloudinary_api_key,
                    cloudinary_api_secret=self.cloudinary_api_secret,
                ),
                BufferExecutor(
                    access_token=self.buffer_access_token,
                    profile_id=self.buffer_profile_id,
                    timezone=self.timezone,
                    dry_run=self.execution_dry_run,
                ),
            ],
        )
        return runtime.run(tasks)

    def _workers(self) -> list[Worker]:
        return [
            Worker(
                worker_id="marketing-design-worker-1",
                department="Design",
                capabilities=["generate_branded_social_image"],
                kpis={"primary": "brand_safe_images_generated"},
            ),
            Worker(
                worker_id="marketing-social-worker-1",
                department="Social",
                capabilities=["publish_social_post"],
                kpis={"primary": "published_posts_with_proof"},
            ),
        ]

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

    def _aeos_spec(self) -> dict[str, Any]:
        return {
            "name": "AUTONOMOUS_EXECUTIVE_OS_SPECIFICATION_v1.0",
            "implemented_department": "Marketing Department",
            "primary_objective": "Acquire additional paying customers.",
            "north_star_priority_order": [
                "Paying Customers",
                "Revenue",
                "Booked Demos",
                "Qualified Leads",
                "WhatsApp Conversations",
                "Website Conversion",
                "Content Performance",
            ],
            "immutable_rules": [
                "Never fabricate metrics.",
                "Every completed action requires evidence.",
                "Every decision must have measurable business intent.",
                "Budget is a hard constraint.",
                "Learning is mandatory.",
                "No repeated failed experiments.",
                "Always optimize customer acquisition.",
            ],
        }

    def _organization(self) -> dict[str, Any]:
        return {
            "operating_model": ["CEO", "Chief of Staff", "Marketing Department", "Workers"],
            "workers": [
                "Creative Director",
                "Copywriter",
                "Designer",
                "Video Producer",
                "Social Media Manager",
                "Promotion Manager",
                "Website Optimizer",
                "Analytics Manager",
                "Growth Strategist",
            ],
            "principle": "Workers execute. Departments own outcomes.",
            "connector_workers": [
                "marketing-design-worker-1",
                "marketing-social-worker-1",
            ],
        }

    def _creative_brief(
        self,
        cta: dict[str, Any],
        brand_intelligence: dict[str, Any],
        whatsapp_bot: dict[str, Any],
        meta_ads: dict[str, Any],
    ) -> dict[str, Any]:
        policy = self._marketing_language_policy(brand_intelligence)
        hebrew_cta = self._hebrew_whatsapp_cta(cta, brand_intelligence)
        verified_whatsapp = bool(isinstance(whatsapp_bot, dict) and whatsapp_bot.get("verified"))
        verified_meta = bool(isinstance(meta_ads, dict) and meta_ads.get("verified"))
        return {
            "campaign_objective": "Acquire qualified law-firm customers.",
            "target_audience": policy["target_audience"],
            "marketing_language": policy["marketing_language"],
            "internal_operating_language": policy["internal_language"],
            "pain": "Israeli law firms lose time qualifying repeated WhatsApp and intake questions.",
            "promise": "Turn WhatsApp inquiries into structured, demo-ready conversations.",
            "offer": "Short WhatsApp walkthrough for law firms.",
            "proof": (
                "No verified outcome proof available yet."
                if not (verified_whatsapp or verified_meta)
                else "Use verified connected acquisition metrics from available sources."
            ),
            "headline": "הפכו פניות WhatsApp לשיחות מסודרות שמובילות לדמו כשיר",
            "supporting_copy": (
                "ChatBot2U עוזר למשרדי עורכי דין לסנן פניות, לענות מהר יותר, "
                "ולהוביל שיחות רלוונטיות לדמו."
            ),
            "cta": hebrew_cta,
            "landing_page": self._whatsapp_link(cta, brand_intelligence),
            "promotion_strategy": "Publish organically first; promote only inside budget rules when Business Value Score supports it.",
            "success_metric": "Additional paying customers, with booked demos and qualified leads as leading indicators.",
            "quality_bar": "Comparable to premium agency advertisements.",
            "creative_director_review": {
                "status": "approved_for_execution",
                "reject_if": [
                    "generic",
                    "low_quality",
                    "poorly_branded",
                    "weak_visual_hierarchy",
                    "unlikely_to_convert",
                ],
            },
        }

    def _marketing_language_policy(self, brand_intelligence: dict[str, Any]) -> dict[str, Any]:
        company = self.company_config.get("company", {})
        marketing = self.company_config.get("marketing", {})
        brand = brand_intelligence.get("brand", {}) if isinstance(brand_intelligence, dict) else {}
        target_audience = (
            brand.get("target_audience")
            or marketing.get("target_audience")
            or [brand.get("audience") or "Israeli law firms"]
        )
        if not isinstance(target_audience, list):
            target_audience = [str(target_audience)]
        return {
            "internal_language": brand.get("internal_language")
            or company.get("internal_language")
            or "English",
            "marketing_language": brand.get("marketing_language")
            or marketing.get("marketing_language")
            or brand.get("language")
            or "Hebrew",
            "default_post_language": brand.get("default_post_language")
            or marketing.get("default_post_language")
            or brand.get("language")
            or "Hebrew",
            "target_country": brand.get("target_country") or marketing.get("target_country") or "Israel",
            "target_audience": target_audience,
        }

    def _brand_cta(self, brand_intelligence: dict[str, Any]) -> dict[str, Any]:
        cta = brand_intelligence.get("cta", {}) if isinstance(brand_intelligence, dict) else {}
        return cta if isinstance(cta, dict) else {}

    def _whatsapp_link(self, cta: dict[str, Any], brand_intelligence: dict[str, Any]) -> str:
        brand_cta = self._brand_cta(brand_intelligence)
        configured_link = str(brand_cta.get("link") or cta.get("link") or "").strip()
        if configured_link:
            return configured_link
        phone = str(brand_cta.get("phone") or cta.get("phone") or "+972559720244")
        normalized = "".join(ch for ch in phone if ch.isdigit())
        return f"https://wa.me/{normalized}"

    def _hebrew_whatsapp_cta(self, cta: dict[str, Any], brand_intelligence: dict[str, Any]) -> str:
        brand_cta = self._brand_cta(brand_intelligence)
        configured = str(brand_cta.get("default_hebrew") or cta.get("default_hebrew") or "").strip()
        if configured:
            return configured
        return f"רוצים לראות איך זה עובד? שלחו הודעה ל-WhatsApp: {self._whatsapp_link(cta, brand_intelligence)}"

    def _content_output(
        self,
        cta: dict[str, Any],
        brand_intelligence: dict[str, Any],
        creative_brief: dict[str, Any],
    ) -> AgentOutput:
        policy = self._marketing_language_policy(brand_intelligence)
        hebrew_cta = self._hebrew_whatsapp_cta(cta, brand_intelligence)
        return AgentOutput(
            agent="Content Agent",
            status="prepared",
            daily_output={
                "creative_brief": creative_brief,
                "publish": "Reel",
                "language": policy["default_post_language"],
                "marketing_language": policy["marketing_language"],
                "internal_language": policy["internal_language"],
                "target_country": policy["target_country"],
                "target_audience": policy["target_audience"],
                "theme": "How AI saves Israeli law firms time before the first consultation.",
                "format_reason": "Short video is the best awareness format for a founder-led validation push.",
                "hebrew_copy": (
                    "עורכי דין מבזבזים שעות על תיאום, שאלות חוזרות וסינון פניות. "
                    "ChatBot2U עוזר להפוך פניות WhatsApp לשיחות מסודרות ודמואים כשירים."
                ),
                "english_internal_rationale": (
                    "Use a concrete time-saving angle to attract law firms that feel intake friction today."
                ),
                "cta": hebrew_cta,
                "cta_channel": "WhatsApp",
                "cta_required": True,
                "whatsapp_link": self._whatsapp_link(cta, brand_intelligence),
                "posting_time": "10:00 Asia/Jerusalem",
                "tomorrow_queue": [
                    "Carousel: 5 intake mistakes law firms can automate",
                    "Story: poll about missed WhatsApp inquiries",
                ],
            },
        )

    def _design_output(
        self,
        brand_intelligence: dict[str, Any],
        task: WorkTask,
        result: ExecutionResult | None,
    ) -> AgentOutput:
        execution_task = task.execution_task
        status = result.status if result else "blocked"
        return AgentOutput(
            agent="Design Agent",
            status=status,
            daily_output={
                "asset_specs": ["Instagram Reel cover", "Story frame", "thumbnail"],
                "brand_source": "Brand Brain" if brand_intelligence else "configured brand defaults",
                "image_provider": execution_task.payload["provider"],
                "image_model": execution_task.payload["model"],
                "image_prompt": execution_task.payload["prompt"],
                "text_policy": execution_task.payload["text_policy"],
                "language_policy": execution_task.payload["language_policy"],
                "alt_text": execution_task.payload["alt_text"],
                "guardrail": (
                    "Use OpenAI for still images, keep Hebrew in captions, and do not publish "
                    "AI-rendered Hebrew text inside generated image pixels."
                ),
                "executed": bool(result and result.status == "completed"),
                "image_path": result.proof.get("image_path") if result else None,
                "worker_id": task.assigned_worker_id,
                "task_id": task.task_id,
                "execution_result": result.to_dict() if result else None,
            },
            error=result.error if result else "waiting_for_design_worker",
        )

    def _image_task(
        self,
        brand_intelligence: dict[str, Any],
        content_output: AgentOutput,
        run_date: str,
    ) -> WorkTask:
        content = content_output.daily_output
        brand_assets = self._brand_assets(brand_intelligence)
        prompt = (
            "OpenAI-generated ChatBot2U branded Instagram visual for Hebrew-speaking Israeli law firms. "
            f"Theme: {content.get('theme')}. "
            "Show WhatsApp client intake becoming a structured qualified demo flow using abstract UI shapes, "
            "simple icons, and practical legal-office context. Use approved ChatBot2U colors and clean B2B SaaS composition. "
            "No text, no letters, no words, no Hebrew characters, no numbers, no CTA text, no subtitles, and no logo text inside the generated image. "
            "All Hebrew copy and WhatsApp CTA must appear only in the Buffer caption or in a deterministic approved overlay outside the image generator."
        )
        execution_task = ExecutionTask(
            id=f"{self.department.lower().replace(' ', '-')}-image-{run_date}",
            connector="ImageExecutor",
            action="generate_branded_social_image",
            initiative=self.initiative,
            expected_business_impact="High",
            delegated_authority_used="marketing.generate_images",
            dry_run=self.execution_dry_run,
            payload={
                "run_date": run_date,
                "provider": "openai",
                "model": self.openai_image_model,
                "prompt": prompt,
                "size": "1024x1024",
                "brand_assets": brand_assets,
                "require_public_url": True,
                "text_policy": "no_model_rendered_text",
                "language_policy": "Hebrew caption only; no generated Hebrew text inside image",
                "alt_text": "ChatBot2U turns WhatsApp inquiries for law firms into structured demo-ready conversations.",
            },
        )
        return WorkTask(
            task_id=execution_task.id,
            department="Design",
            capability="generate_branded_social_image",
            title="Generate brand-safe Instagram image",
            execution_task=execution_task,
            priority=TaskPriority.HIGH,
            max_retries=3,
        )

    def _brand_assets(self, brand_intelligence: dict[str, Any]) -> dict[str, Any]:
        colors = brand_intelligence.get("colors") or brand_intelligence.get("palette") or ["#1D4ED8", "#111827"]
        logo = (
            brand_intelligence.get("logo")
            or brand_intelligence.get("logo_path")
            or "knowledge/companies/chatbot2u/brand/logo/logo-light.svg"
        )
        return {
            "colors": colors,
            "logo": logo,
            "source": "Brand Brain" if brand_intelligence else "configured brand defaults",
        }

    def _video_output(self, cta: dict[str, Any], brand_intelligence: dict[str, Any]) -> AgentOutput:
        policy = self._marketing_language_policy(brand_intelligence)
        hebrew_cta = self._hebrew_whatsapp_cta(cta, brand_intelligence)
        return AgentOutput(
            agent="Video Agent",
            status="prepared",
            daily_output={
                "language": policy["default_post_language"],
                "renderer": "HeyGen",
                "format": "Instagram Reels",
                "aspect_ratio": "9:16",
                "resolution": "1080x1920",
                "subtitles": False,
                "captions": "none",
                "safe_area": "Keep presenter and product visuals inside the Instagram Reels safe area.",
                "heygen_script": (
                    "משרדי עורכי דין מאבדים זמן על אותן שאלות פתיחה שוב ושוב. "
                    "ChatBot2U הופך פניות WhatsApp לשיחות מסודרות שמובילות לדמו כשיר. "
                    f"{hebrew_cta}"
                ),
                "storyboard": [
                    "Problem: repeated intake messages",
                    "Solution: AI WhatsApp qualification",
                    "Outcome: one cleaner path to a booked demo",
                ],
                "voice_over": "Confident founder-led Hebrew, practical and direct.",
                "thumbnail": "Law firm intake before and after ChatBot2U.",
                "cta": hebrew_cta,
            },
        )

    def _social_output(
        self,
        content_output: AgentOutput,
        image_result: ExecutionResult | None,
        result: ExecutionResult | None,
        run_date: str,
    ) -> AgentOutput:
        if image_result is None or image_result.status != "completed":
            blocked_result = result or ExecutionResult.blocked(
                self._buffer_task(content_output, image_result, run_date=run_date).execution_task,
                timezone=self.timezone,
                error="Image proof is required before publishing Instagram content.",
                next_retry="after ImageExecutor completes",
                result={
                    "required_connector": "ImageExecutor",
                    "image_status": image_result.status if image_result else "missing",
                    "image_error": image_result.error if image_result else None,
                },
            )
            return AgentOutput(
                agent="Social Agent",
                status="blocked",
                daily_output={
                    "executed": False,
                    "reason": "Image proof is required before publishing Instagram content.",
                    "connector": "BufferExecutor",
                    "recorded_urls": [],
                    "recorded_post_ids": [],
                    "image_path": None,
                    "caption_hash": self._caption_hash(content_output),
                    "execution_result": blocked_result.to_dict(),
                },
                error="waiting_for_image_executor",
            )

        if result is None:
            result = ExecutionResult.blocked(
                self._buffer_task(content_output, image_result, run_date=run_date).execution_task,
                timezone=self.timezone,
                error="Social worker has not executed Buffer task yet.",
                next_retry="next workforce scheduler run",
            )

        return AgentOutput(
            agent="Social Agent",
            status=result.status,
            daily_output={
                "executed": result.status == "completed",
                "connector": "BufferExecutor",
                "recorded_urls": (
                    [result.proof["instagram_url"]]
                    if result.proof.get("instagram_url")
                    else [result.proof["buffer_post_url"]]
                    if result.proof.get("buffer_post_url")
                    else []
                ),
                "recorded_post_ids": (
                    [result.artifact_ids["buffer_update_id"]]
                    if result.artifact_ids.get("buffer_update_id")
                    else []
                ),
                "image_path": image_result.proof.get("image_path"),
                "caption_hash": self._caption_hash(content_output),
                "execution_result": result.to_dict(),
            },
            error=result.error,
        )

    def _buffer_task(
        self,
        content_output: AgentOutput,
        image_result: ExecutionResult | None,
        run_date: str,
    ) -> WorkTask:
        content = content_output.daily_output
        image_path = image_result.proof.get("image_path") if image_result else ""
        image_sha256 = image_result.proof.get("sha256") if image_result else ""
        public_url = image_result.proof.get("public_url") if image_result else ""
        media: dict[str, str] = {}
        if public_url:
            media["photo"] = str(public_url)
        execution_task = ExecutionTask(
            id=f"{self.department.lower().replace(' ', '-')}-buffer-reel-{run_date}",
            connector="BufferExecutor",
            action="publish_social_post",
            initiative=self.initiative,
            expected_business_impact="High",
            delegated_authority_used="marketing.publish_posts / marketing.publish_reels",
            dry_run=self.execution_dry_run,
            payload={
                "timezone": self.timezone,
                "text": "\n\n".join(
                    [
                        str(content.get("hebrew_copy", "")).strip(),
                        str(content.get("cta", "")).strip(),
                    ]
                ).strip(),
                "publish_now": True,
                "format": content.get("publish"),
                "theme": content.get("theme"),
                "media": media,
                "image_path": image_path,
                "image_sha256": image_sha256,
                "public_url": public_url,
                "caption_hash": self._caption_hash(content_output),
                "require_media": True,
                "require_public_media": True,
            },
        )
        return WorkTask(
            task_id=execution_task.id,
            department="Social",
            capability="publish_social_post",
            title="Publish Instagram post through Buffer",
            execution_task=execution_task,
            priority=TaskPriority.HIGH,
            dependencies=[f"{self.department.lower().replace(' ', '-')}-image-{run_date}"],
            max_retries=3,
        )

    def _result_for(self, results: list[ExecutionResult], connector: str) -> ExecutionResult | None:
        for result in results:
            if result.connector == connector:
                return result
        return None

    def _caption_hash(self, content_output: AgentOutput) -> str:
        content = content_output.daily_output
        caption = "\n\n".join(
            [
                str(content.get("hebrew_copy", "")).strip(),
                str(content.get("cta", "")).strip(),
            ]
        ).strip()
        return sha256(caption.encode("utf-8")).hexdigest()

    def _budget_status(self, meta_ads: dict[str, Any]) -> dict[str, Any]:
        marketing_budget = self.company_config.get("marketing", {}).get("budget_rule", {})
        ads_authority = (
            self.objectives_config.get("delegated_authority", {})
            .get("ads", {})
        )
        daily_limit = int(
            ads_authority.get("daily_budget_limit_ils")
            or marketing_budget.get("amount_ils_per_day")
            or 20
        )
        monthly_limit = int(ads_authority.get("total_monthly_budget_ils") or daily_limit * 30)
        verified = bool(isinstance(meta_ads, dict) and meta_ads.get("verified"))
        campaign_status = str(meta_ads.get("campaign_status") or "unknown") if isinstance(meta_ads, dict) else "unknown"
        current_spend = meta_ads.get("current_spend_ils") if verified else None
        remaining_monthly = (
            max(monthly_limit - int(current_spend), 0)
            if isinstance(current_spend, int)
            else None
        )
        return {
            "currency": "ILS",
            "daily_budget_limit_ils": daily_limit,
            "monthly_budget_limit_ils": monthly_limit,
            "current_spend_ils": current_spend,
            "remaining_monthly_budget_ils": remaining_monthly,
            "saturday": marketing_budget.get("saturday", "no spend"),
            "friday": marketing_budget.get("friday", "morning only"),
            "one_active_promotion_per_asset": True,
            "one_active_campaign_limit": True,
            "campaign_status": campaign_status,
            "verified": verified,
            "status": "verified" if verified else "unavailable",
            "blocking_issue": None if verified else "No verified Meta spend data available.",
        }

    def _content_intelligence(
        self,
        whatsapp_bot: dict[str, Any],
        meta_ads: dict[str, Any],
        buffer_result: ExecutionResult | None,
    ) -> dict[str, Any]:
        verified_whatsapp = bool(isinstance(whatsapp_bot, dict) and whatsapp_bot.get("verified"))
        verified_meta = bool(isinstance(meta_ads, dict) and meta_ads.get("verified"))
        published = buffer_result is not None and buffer_result.status == "completed"
        proof = buffer_result.proof if published else {}
        if not (verified_whatsapp or verified_meta):
            return {
                "status": "unavailable",
                "reason": "No verified content, WhatsApp, or campaign outcome data available yet.",
                "ranked_assets": [],
                "business_value_score": None,
                "predicted_roi": None,
                "predicted_demo_probability": None,
                "metrics": {
                    "reach": None,
                    "impressions": None,
                    "saves": None,
                    "shares": None,
                    "comments": None,
                    "profile_visits": None,
                    "whatsapp_clicks": None,
                    "demo_requests": None,
                    "customers": None,
                },
                "published_asset_under_review": {
                    "instagram_url": proof.get("instagram_url"),
                    "buffer_update_id": proof.get("buffer_update_id"),
                    "image_sha256": proof.get("image_sha256"),
                } if published else None,
                "next_automatic_action": "Retry analytics collection after Instagram, Meta, and WhatsApp attribution are connected.",
            }

        today = whatsapp_bot.get("today", {}) if isinstance(whatsapp_bot, dict) else {}
        whatsapp_clicks = _safe_int(today.get("conversations"))
        demo_requests = _safe_int(today.get("demo_requests") or today.get("demo_bookings"))
        customers = _safe_int(today.get("customers"))
        business_value_score = min(
            100,
            ((whatsapp_clicks or 0) * 2)
            + ((demo_requests or 0) * 20)
            + ((customers or 0) * 50),
        )
        return {
            "status": "verified",
            "reason": "Calculated from verified acquisition signals.",
            "ranked_assets": [
                {
                    "rank": 1,
                    "instagram_url": proof.get("instagram_url") if published else None,
                    "buffer_update_id": proof.get("buffer_update_id") if published else None,
                    "business_value_score": business_value_score,
                }
            ],
            "business_value_score": business_value_score,
            "predicted_roi": "pending_attribution",
            "predicted_demo_probability": None if demo_requests is None else min(1.0, demo_requests / 10),
            "metrics": {
                "reach": None,
                "impressions": None,
                "saves": None,
                "shares": None,
                "comments": None,
                "profile_visits": None,
                "whatsapp_clicks": whatsapp_clicks,
                "demo_requests": demo_requests,
                "customers": customers,
            },
            "published_asset_under_review": {
                "instagram_url": proof.get("instagram_url"),
                "buffer_update_id": proof.get("buffer_update_id"),
                "image_sha256": proof.get("image_sha256"),
            } if published else None,
            "next_automatic_action": "Rank all content daily and promote only when score and budget rules allow it.",
        }

    def _campaign_lifecycle(
        self,
        execution_results: list[ExecutionResult],
        content_intelligence: dict[str, Any],
    ) -> dict[str, Any]:
        completed_actions = {result.action for result in execution_results if result.status == "completed"}
        return {
            "steps": [
                "Research",
                "Creative Brief",
                "Copy",
                "Image",
                "Video",
                "Brand Validation",
                "Conversion Review",
                "Publish",
                "Promote",
                "Measure",
                "Learn",
            ],
            "current_state": {
                "research": "completed",
                "creative_brief": "completed",
                "copy": "completed",
                "image": "completed" if "generate_branded_social_image" in completed_actions else "blocked",
                "video": "specified",
                "brand_validation": "completed" if "generate_branded_social_image" in completed_actions else "pending",
                "conversion_review": content_intelligence.get("status", "unavailable"),
                "publish": "completed" if "publish_social_post" in completed_actions else "blocked",
                "promote": "blocked",
                "measure": content_intelligence.get("status", "unavailable"),
                "learn": "pending_verified_outcomes",
            },
        }

    def _hypothesis_register(self, content_intelligence: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            {
                "hypothesis": "Hebrew WhatsApp-intake content for Israeli law firms will increase qualified WhatsApp conversations.",
                "status": "running" if content_intelligence.get("published_asset_under_review") else "pending_execution",
                "success_metric": "Qualified leads, booked demos, and paying customers.",
                "result": "pending_verified_attribution",
                "confidence": "medium",
            }
        ]

    def _decision_ledger(
        self,
        content_output: AgentOutput,
        creative_brief: dict[str, Any],
        content_intelligence: dict[str, Any],
    ) -> list[dict[str, Any]]:
        content = content_output.daily_output
        return [
            {
                "decision": "Publish Hebrew WhatsApp-intake content for Israeli law firms.",
                "reason": creative_brief["pain"],
                "business_intent": "Increase qualified law-firm WhatsApp conversations that can become booked demos and customers.",
                "prediction": "This content should increase qualified WhatsApp conversations once attribution is connected.",
                "success_metric": creative_brief["success_metric"],
                "result": content_intelligence.get("status"),
                "learning": "pending_verified_outcomes",
                "caption_hash": self._caption_hash(content_output),
                "cta": content.get("cta"),
            }
        ]

    def _business_memory(self, content_intelligence: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            {
                "date": datetime.now(ZoneInfo(self.timezone)).date().isoformat(),
                "learning": "No verified performance learning yet; attribution remains the highest leverage measurement gap.",
                "confidence": "low" if content_intelligence.get("status") == "unavailable" else "medium",
                "evidence": content_intelligence.get("published_asset_under_review"),
                "action": "Keep collecting evidence and connect WhatsApp/Instagram attribution.",
            }
        ]

    def _ads_output(
        self,
        meta_ads: dict[str, Any],
        budget_status: dict[str, Any],
        content_intelligence: dict[str, Any],
    ) -> AgentOutput:
        verified_campaign = bool(meta_ads.get("verified") and meta_ads.get("campaign_status") == "active")
        score = content_intelligence.get("business_value_score")
        promote = bool(isinstance(score, int) and score >= 90 and budget_status.get("verified"))
        return AgentOutput(
            agent="Ads Agent",
            status="blocked",
            daily_output={
                "campaign_status": meta_ads.get("campaign_status", "unknown"),
                "executed": False,
                "reason": (
                    "MetaExecutor is not implemented/configured. A campaign cannot be created or reported active."
                ),
                "promotion_decision": "promote" if promote else "do_not_promote",
                "business_value_score": score,
                "budget_status": budget_status,
                "budget_rule": "Do not exceed ILS 20/day or ILS 600/month. No Saturday spend. Friday morning only. One active promotion per asset.",
                "verified_active_campaign": verified_campaign,
            },
            error="waiting_for_meta_executor",
        )

    def _analytics_output(
        self,
        whatsapp_bot: dict[str, Any],
        meta_ads: dict[str, Any],
        content_intelligence: dict[str, Any],
    ) -> AgentOutput:
        verified = bool(whatsapp_bot.get("verified")) or bool(meta_ads.get("verified"))
        return AgentOutput(
            agent="Analytics Agent",
            status="collected" if verified else "blocked",
            daily_output={
                "content_intelligence": content_intelligence,
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
            "completed": "executed",
            "prepared": "internal_memory",
            "prepared_with_brand_defaults": "internal_memory",
            "blocked": "blocked",
            "failed": "failed",
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
            "Design Agent": "Blocked branded image generation",
            "Video Agent": "Prepared HeyGen video script and storyboard",
            "Social Agent": "Blocked Instagram publishing",
            "Ads Agent": "Blocked paid promotion",
            "Analytics Agent": "Blocked verified marketing outcome analysis",
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
            return "Retry automatically after Buffer credentials are configured and dry-run is disabled."
        if output.agent == "Design Agent" and output.status == "blocked":
            return "Retry automatically after ImageExecutor is enabled and dry-run is disabled."
        if output.agent == "Design Agent" and output.status == "failed":
            return "Fix brand validation or image generation error before retry."
        if output.agent == "Design Agent" and output.status == "completed":
            return "Pass image proof to BufferExecutor."
        if output.agent == "Social Agent" and output.status == "failed":
            return "Retry Buffer publishing tomorrow 08:00 unless the error is non-retryable."
        if output.agent == "Social Agent" and output.status == "completed":
            return "Record Buffer URL/post ID and measure WhatsApp demo intent."
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
    decision_context.summary["aeos_spec"] = payload.get("aeos_spec", {})
    decision_context.summary["organization"] = payload.get("organization", {})
    decision_context.summary["creative_brief"] = payload.get("creative_brief", {})
    decision_context.summary["campaign_lifecycle"] = payload.get("campaign_lifecycle", {})
    decision_context.summary["budget_status"] = payload.get("budget_status", {})
    decision_context.summary["content_intelligence"] = payload.get("content_intelligence", {})
    decision_context.summary["hypothesis_register"] = payload.get("hypothesis_register", [])
    decision_context.summary["decision_ledger"] = payload.get("decision_ledger", [])
    decision_context.summary["business_memory"] = payload.get("business_memory", [])
    decision_context.summary["connector_execution"] = {
        "results": [result.to_dict() for result in output.execution_results],
        "proof_required": {
            "published_reel": [
                "buffer_update_id",
                "buffer_post_url",
                "publish_status",
                "timestamp",
                "caption_hash",
                "image_sha256",
                "public_url",
                "worker_id",
            ],
            "started_campaign": ["campaign_id", "budget", "status"],
            "generated_video": ["mp4_path", "storage_location", "execution_log"],
        },
    }
    decision_context.summary["workforce"] = output.workforce
    decision_context.summary["execution_departments"] = {
        "frozen_executive_layer": True,
        "active_department": "Marketing Operations",
        "department_status": output.status,
        "success_criterion": (
            "Operate ChatBot2U marketing for 30 consecutive days without operational intervention "
            "while increasing qualified leads, booked demos, and paying customers."
        ),
    }
    executed = [
        action["action"]
        for action in output.action_log
        if action.get("status") == "executed"
    ]
    internal_memory = [
        action["action"]
        for action in output.action_log
        if action.get("status") == "internal_memory"
    ]
    blocked = [
        action["action"]
        for action in output.action_log
        if action.get("status") == "blocked"
    ]
    failed = [
        action["action"]
        for action in output.action_log
        if action.get("status") == "failed"
    ]
    autonomous_work_kpi = _autonomous_work_completion_rate(output.action_log)
    decision_context.summary["executed_actions_today"] = executed or ["none"]
    decision_context.summary["prepared_actions"] = []
    decision_context.summary["internal_memory_tasks"] = internal_memory
    decision_context.summary["blocked_actions"] = blocked
    decision_context.summary["failed_actions"] = failed
    decision_context.summary["autonomous_work_completion_rate"] = autonomous_work_kpi
    revenue_influence = _revenue_influence_score(decision_context, output.action_log)
    decision_context.summary["revenue_influence_score"] = revenue_influence
    business_autonomy = _business_autonomy_index(
        autonomous_work=autonomous_work_kpi,
        revenue_influence=revenue_influence,
        decision_context=decision_context,
    )
    decision_context.summary["business_autonomy_index"] = business_autonomy
    self_evaluation = _self_evaluation(
        action_log=output.action_log,
        execution_results=[result.to_dict() for result in output.execution_results],
        revenue_influence=revenue_influence,
        blocked=blocked,
        failed=failed,
    )
    decision_context.summary["self_evaluation"] = self_evaluation
    if isinstance(decision_context.summary.get("execution_reality"), dict):
        decision_context.summary["execution_reality"]["prepared_actions"] = []
        decision_context.summary["execution_reality"]["internal_memory_tasks"] = internal_memory
        decision_context.summary["execution_reality"][
            "autonomous_work_completion_rate"
        ] = autonomous_work_kpi
        decision_context.summary["execution_reality"]["revenue_influence_score"] = revenue_influence
        decision_context.summary["execution_reality"]["business_autonomy_index"] = business_autonomy
        decision_context.summary["execution_reality"]["self_evaluation"] = self_evaluation
    decision_context.daily_report.autonomous_action_log.extend(output.action_log)


def _autonomous_work_completion_rate(action_log: list[dict[str, Any]]) -> dict[str, Any]:
    connector_facing = [
        action
        for action in action_log
        if action.get("status") in {"executed", "blocked", "failed"}
    ]
    planned = len(connector_facing)
    completed = sum(1 for action in connector_facing if action.get("status") == "executed")
    blocked = sum(1 for action in connector_facing if action.get("status") == "blocked")
    failed = sum(1 for action in connector_facing if action.get("status") == "failed")
    success_rate = round(completed / planned, 2) if planned else None
    return {
        "metric": "Autonomous Work Completion Rate",
        "planned_tasks": planned,
        "completed_automatically": completed,
        "blocked": blocked,
        "failed": failed,
        "success_rate": success_rate,
        "success_rate_percent": int(success_rate * 100) if success_rate is not None else None,
        "target_success_rate_percent": 95,
        "definition": (
            "Completed connector-facing work divided by completed, blocked, and failed connector-facing work."
        ),
        "excludes": "Internal memory tasks and prepared payloads that have no execution proof.",
    }


def _revenue_influence_score(
    decision_context: DecisionContext,
    action_log: list[dict[str, Any]],
) -> dict[str, Any]:
    whatsapp_bot = decision_context.summary.get("whatsapp_bot", {})
    verified_funnel = bool(isinstance(whatsapp_bot, dict) and whatsapp_bot.get("verified"))
    today = whatsapp_bot.get("today", {}) if isinstance(whatsapp_bot, dict) else {}
    completed_actions = [
        action for action in action_log if action.get("status") == "executed"
    ]
    qualified_leads = _safe_int(today.get("qualified_leads")) if verified_funnel else None
    booked_demos = (
        _safe_int(today.get("demo_bookings") or today.get("demos_booked"))
        if verified_funnel
        else None
    )
    customers = _safe_int(today.get("customers")) if verified_funnel else None
    if not verified_funnel:
        return {
            "metric": "Revenue Influence Score",
            "score": None,
            "status": "unavailable",
            "reason": "No verified funnel data connected.",
            "traceability_required": ["post", "campaign", "reel", "website_change", "outreach"],
            "qualified_leads": None,
            "booked_demos": None,
            "customers": None,
            "influencing_actions": len(completed_actions),
        }

    score = min(
        100,
        (len(completed_actions) * 5)
        + ((qualified_leads or 0) * 10)
        + ((booked_demos or 0) * 25)
        + ((customers or 0) * 50),
    )
    return {
        "metric": "Revenue Influence Score",
        "score": score,
        "status": "verified",
        "reason": "Calculated from verified funnel events and completed AI actions.",
        "traceability_required": ["post", "campaign", "reel", "website_change", "outreach"],
        "qualified_leads": qualified_leads,
        "booked_demos": booked_demos,
        "customers": customers,
        "influencing_actions": len(completed_actions),
    }


def _safe_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _self_evaluation(
    *,
    action_log: list[dict[str, Any]],
    execution_results: list[dict[str, Any]],
    revenue_influence: dict[str, Any],
    blocked: list[str],
    failed: list[str],
) -> dict[str, Any]:
    completed_actions = [
        action for action in action_log if action.get("status") == "executed"
    ]
    completed_results = [
        result for result in execution_results if result.get("status") == "completed"
    ]
    customer_acquisition_results = [
        result
        for result in completed_results
        if (
            result.get("action") == "publish_social_post"
            and isinstance(result.get("proof"), dict)
            and result["proof"].get("buffer_post_url")
        )
        or (
            result.get("action") == "start_meta_campaign"
            and isinstance(result.get("proof"), dict)
            and result["proof"].get("campaign_id")
        )
    ]
    proof_items = [
        {
            "action": result.get("action"),
            "connector": result.get("connector"),
            "proof": result.get("proof", {}),
        }
        for result in customer_acquisition_results
    ]
    has_verified_revenue = revenue_influence.get("status") == "verified" and bool(
        (revenue_influence.get("qualified_leads") or 0)
        or (revenue_influence.get("booked_demos") or 0)
        or (revenue_influence.get("customers") or 0)
    )
    has_customer_acquisition_artifact = bool(customer_acquisition_results)
    if has_verified_revenue:
        value_status = "yes"
        value_answer = "Yes. Verified funnel data shows measurable customer-acquisition movement."
    elif has_customer_acquisition_artifact:
        value_status = "partial"
        value_answer = "Partially. A customer-acquisition artifact was completed, but revenue attribution is not connected yet."
    else:
        value_status = "no"
        value_answer = "No. No verified customer-acquisition outcome or completed business artifact was created."

    if completed_actions:
        biggest_positive = str(completed_actions[0].get("action", "Completed autonomous action"))
    else:
        biggest_positive = "No completed autonomous action produced measurable business value."

    wrong_decision = "No wrong execution decision detected from available evidence."
    if failed:
        wrong_decision = f"Execution failed on: {failed[0]}."
    elif blocked:
        wrong_decision = f"The system attempted work that is still blocked: {blocked[0]}."
    elif not has_verified_revenue:
        wrong_decision = "The system still cannot prove which activity created leads, demos, or customers."

    blocker = None
    if value_status == "no":
        blocker = "Remove the highest-impact blocker: closed-loop attribution from content to WhatsApp to demo to customer."
    elif value_status == "partial":
        blocker = "Connect attribution so completed artifacts can be judged by customer-acquisition outcomes."

    return {
        "questions": [
            "Did I create measurable business value today?",
            "What evidence supports that?",
            "Which decision had the biggest positive impact?",
            "Which decision was wrong?",
            "What will I do differently tomorrow?",
        ],
        "did_create_measurable_business_value_today": value_status,
        "business_value_answer": value_answer,
        "evidence_supporting_value": proof_items,
        "biggest_positive_impact_decision": biggest_positive,
        "decision_that_was_wrong": wrong_decision,
        "do_differently_tomorrow": (
            "Prioritize the single capability that increases the probability of acquiring another paying customer."
        ),
        "highest_impact_blocker": blocker,
        "optimization_principle": "Never optimize activity. Always optimize customer acquisition.",
    }


def _business_autonomy_index(
    *,
    autonomous_work: dict[str, Any],
    revenue_influence: dict[str, Any],
    decision_context: DecisionContext,
) -> dict[str, Any]:
    planning = 100
    execution = int(autonomous_work.get("success_rate_percent") or 0)
    data_confidence = decision_context.summary.get("data_confidence", {})
    learning = {"High": 90, "Medium": 65, "Low": 25}.get(str(data_confidence.get("level")), 25)
    revenue = int(revenue_influence.get("score") or 0)
    overall = round((planning * 0.2) + (execution * 0.4) + (learning * 0.2) + (revenue * 0.2))
    return {
        "metric": "Business Autonomy Index",
        "planning_percent": planning,
        "execution_percent": execution,
        "learning_percent": learning,
        "revenue_influence_percent": revenue,
        "overall_percent": overall,
        "threshold_for_autonomous_operator": 90,
        "definition": (
            "Weighted score for whether the AI Executive OS can turn plans into verified business outcomes."
        ),
    }
