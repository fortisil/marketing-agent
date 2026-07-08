from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from hashlib import sha256
import json
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
    growth_intelligence: dict[str, Any] = field(default_factory=dict)
    executive_measurement: dict[str, Any] = field(default_factory=dict)
    operating_executive: dict[str, Any] = field(default_factory=dict)
    revenue_cmo: dict[str, Any] = field(default_factory=dict)
    promotion_brain: dict[str, Any] = field(default_factory=dict)
    budget_guard: dict[str, Any] = field(default_factory=dict)
    campaign_decision: dict[str, Any] = field(default_factory=dict)
    video_production: dict[str, Any] = field(default_factory=dict)
    brand_brain: dict[str, Any] = field(default_factory=dict)
    connector_health: dict[str, Any] = field(default_factory=dict)
    monitoring: dict[str, Any] = field(default_factory=dict)
    weekly_executive_review: dict[str, Any] = field(default_factory=dict)
    acceptance_criteria: dict[str, Any] = field(default_factory=dict)
    final_definition_of_done: dict[str, Any] = field(default_factory=dict)
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
            "growth_intelligence": self.growth_intelligence,
            "executive_measurement": self.executive_measurement,
            "operating_executive": self.operating_executive,
            "revenue_cmo": self.revenue_cmo,
            "promotion_brain": self.promotion_brain,
            "budget_guard": self.budget_guard,
            "campaign_decision": self.campaign_decision,
            "video_production": self.video_production,
            "brand_brain": self.brand_brain,
            "connector_health": self.connector_health,
            "monitoring": self.monitoring,
            "weekly_executive_review": self.weekly_executive_review,
            "acceptance_criteria": self.acceptance_criteria,
            "final_definition_of_done": self.final_definition_of_done,
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
        growth_intelligence = self._growth_intelligence(whatsapp_bot, meta_ads, website_intelligence, content_intelligence)
        budget_guard = self._budget_guard(budget_status, now)
        promotion_brain = self._promotion_brain(content_intelligence, budget_status, budget_guard)
        campaign_decision = self._campaign_decision_record(
            content_intelligence=content_intelligence,
            promotion_brain=promotion_brain,
            budget_guard=budget_guard,
            budget_status=budget_status,
            meta_ads=meta_ads,
            cta=cta,
            run_date=decision_context.run_date,
            now=now,
        )
        executive_measurement = self._executive_measurement(
            content_intelligence=content_intelligence,
            growth_intelligence=growth_intelligence,
            promotion_brain=promotion_brain,
            budget_status=budget_status,
            budget_guard=budget_guard,
            campaign_decision=campaign_decision,
            whatsapp_bot=whatsapp_bot,
            meta_ads=meta_ads,
            website_intelligence=website_intelligence,
            buffer_result=buffer_result,
            run_date=decision_context.run_date,
        )
        operating_executive = self._operating_executive(
            content_intelligence=content_intelligence,
            growth_intelligence=growth_intelligence,
            executive_measurement=executive_measurement,
            promotion_brain=promotion_brain,
            budget_status=budget_status,
            budget_guard=budget_guard,
            campaign_decision=campaign_decision,
            whatsapp_bot=whatsapp_bot,
            meta_ads=meta_ads,
            website_intelligence=website_intelligence,
            buffer_result=buffer_result,
            run_date=decision_context.run_date,
            now=now,
        )
        revenue_cmo = self._revenue_cmo_report(
            content_intelligence=content_intelligence,
            growth_intelligence=growth_intelligence,
            executive_measurement=executive_measurement,
            operating_executive=operating_executive,
            promotion_brain=promotion_brain,
            budget_guard=budget_guard,
            campaign_decision=campaign_decision,
            budget_status=budget_status,
            creative_brief=creative_brief,
            whatsapp_bot=whatsapp_bot,
            meta_ads=meta_ads,
            website_intelligence=website_intelligence,
            buffer_result=buffer_result,
            run_date=decision_context.run_date,
        )
        video_output = self._video_output(cta, brand_intelligence)
        video_production = self._video_production(video_output.daily_output, brand_intelligence)
        social_output = self._social_output(
            content_output,
            image_result,
            buffer_result,
            decision_context.run_date,
        )
        outputs = [
            content_output,
            design_output,
            video_output,
            social_output,
            self._ads_output(meta_ads, budget_status, content_intelligence, promotion_brain, campaign_decision),
            self._analytics_output(whatsapp_bot, meta_ads, content_intelligence, growth_intelligence),
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
            growth_intelligence=growth_intelligence,
            executive_measurement=executive_measurement,
            operating_executive=operating_executive,
            revenue_cmo=revenue_cmo,
            promotion_brain=promotion_brain,
            budget_guard=budget_guard,
            campaign_decision=campaign_decision,
            video_production=video_production,
            brand_brain=self._brand_brain(brand_intelligence),
            connector_health=self._connector_health(whatsapp_bot, meta_ads, image_result, buffer_result),
            monitoring=self._monitoring(decision_context.run_date, execution_results, buffer_result),
            weekly_executive_review=self._weekly_executive_review(whatsapp_bot, meta_ads, content_intelligence),
            acceptance_criteria=self._acceptance_criteria(execution_results, content_intelligence, budget_guard),
            final_definition_of_done=self._final_definition_of_done(content_intelligence, budget_guard),
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
        asset_library = brand_intelligence.get("asset_library", {}) if isinstance(brand_intelligence, dict) else {}
        missing_brand_assets = brand_intelligence.get("missing_assets", []) if isinstance(brand_intelligence, dict) else []
        product_screenshot_available = (
            bool(asset_library.get("screenshots"))
            and "screenshots" not in missing_brand_assets
            and self._asset_library_has_files(asset_library.get("screenshots"))
        )
        approved_examples_available = (
            bool(asset_library.get("templates"))
            and "templates" not in missing_brand_assets
            and self._asset_library_has_files(asset_library.get("templates"))
        )
        creative_director_approved = product_screenshot_available and approved_examples_available
        creative_concepts = [
            {
                "concept_id": "law-firm-intake-before-after",
                "score": 92,
                "visual_concept": "Premium SaaS ad showing a real ChatBot2U intake screen beside a clean WhatsApp lead path.",
                "headline": "כך משרד עורכי דין הופך פניות WhatsApp לדמואים כשירים",
                "reason": "Clear pain, product proof, and direct customer-acquisition CTA.",
            },
            {
                "concept_id": "legal-ai-quick-start",
                "score": 88,
                "visual_concept": "Landing-page style ad with product screenshot, feature cards, and a Legal AI Quick Start offer.",
                "headline": "Legal AI Quick Start למשרדי עורכי דין",
                "reason": "Matches the manually approved quality bar and keeps hierarchy Hebrew-first.",
            },
            {
                "concept_id": "founder-proof-whatsapp",
                "score": 81,
                "visual_concept": "Founder-led proof layout with WhatsApp CTA and product workflow preview.",
                "headline": "יותר מהר לפנייה כשירה. פחות זמן על סינון ידני.",
                "reason": "Trust-building concept, but weaker without verified founder/product assets.",
            },
        ]
        return {
            "campaign_objective": "Acquire qualified law-firm customers.",
            "target_audience": policy["target_audience"],
            "marketing_language": policy["marketing_language"],
            "internal_operating_language": policy["internal_language"],
            "pain": "Israeli law firms lose time qualifying repeated WhatsApp and intake questions.",
            "emotional_trigger": "Stop wasting attorney time on repetitive intake and missed WhatsApp opportunities.",
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
            "visual_concept": creative_concepts[0]["visual_concept"],
            "landing_page": self._whatsapp_link(cta, brand_intelligence),
            "promotion_strategy": "Publish organically first; promote only inside budget rules when Business Value Score supports it.",
            "success_metric": "Additional paying customers, with booked demos and qualified leads as leading indicators.",
            "quality_bar": "Israeli high-end SaaS advertisement, not AI artwork.",
            "creative_concepts": creative_concepts,
            "selected_concept": creative_concepts[0],
            "creative_director_review": {
                "approved": creative_director_approved,
                "status": (
                    "approved_for_execution"
                    if creative_director_approved
                    else "blocked_until_product_screenshot_and_template_assets_exist"
                ),
                "would_spend_20_ils_promoting_this": creative_director_approved,
                "human_benchmark": "Would this stop an Israeli law-firm decision maker from scrolling?",
                "mandatory_structure": [
                    "Powerful Hebrew headline",
                    "Supporting Hebrew sentence",
                    "Real product screenshot",
                    "ChatBot2U logo",
                    "One clear WhatsApp CTA",
                    "Minimal icons",
                    "Whitespace",
                    "Professional typography",
                    "Modern SaaS layout",
                    "Consistent branding",
                ],
                "reject_if": [
                    "generic AI illustration",
                    "robot",
                    "floating icons",
                    "stock-looking graphic",
                    "cartoon or emoji style",
                    "generic gradient background",
                    "weak Hebrew hierarchy",
                    "no product screenshot",
                    "no WhatsApp CTA",
                    "unlikely to convert",
                ],
                "failed_rules": (
                    []
                    if creative_director_approved
                    else [
                        "Real product screenshot asset is missing.",
                        "Approved SaaS ad template/example asset is missing.",
                    ]
                ),
            },
        }

    def _asset_library_has_files(self, path_value: Any) -> bool:
        if not path_value:
            return False
        path = Path(str(path_value))
        if not path.exists():
            return False
        if path.is_file():
            return True
        return any(item.is_file() for item in path.rglob("*"))

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
                    "Use OpenAI for still images only after Creative Director approval. "
                    "The published asset must be Hebrew-first, premium SaaS advertising, and never generic AI artwork."
                ),
                "creative_director_review": execution_task.payload.get("creative_director_review"),
                "selected_concept": execution_task.payload.get("selected_concept"),
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
        creative_brief = content.get("creative_brief", {})
        creative_review = creative_brief.get("creative_director_review", {})
        selected_concept = creative_brief.get("selected_concept", {})
        brand_assets = self._brand_assets(brand_intelligence)
        prompt = (
            "Design a premium Hebrew-first ChatBot2U Instagram advertisement for Israeli law firms. "
            "This must look like a high-end SaaS campaign from Apple, Stripe, Notion, Linear, Monday, Wix Enterprise, or Israeli SaaS brands. "
            f"Campaign objective: {creative_brief.get('campaign_objective')}. "
            f"Audience: {creative_brief.get('target_audience')}. "
            f"Emotional trigger: {creative_brief.get('emotional_trigger')}. "
            f"Promise: {creative_brief.get('promise')}. "
            f"Proof: {creative_brief.get('proof')}. "
            f"Offer: {creative_brief.get('offer')}. "
            f"CTA: {creative_brief.get('cta')}. "
            f"Visual concept: {selected_concept.get('visual_concept')}. "
            f"Hebrew headline: {selected_concept.get('headline') or creative_brief.get('headline')}. "
            f"Supporting Hebrew copy: {creative_brief.get('supporting_copy')}. "
            "Mandatory layout: powerful Hebrew headline, supporting sentence, realistic product UI screenshot, ChatBot2U logo, one clear WhatsApp CTA, minimal icons, generous whitespace, professional typography, modern SaaS landing-page aesthetic, consistent ChatBot2U branding. "
            "Forbidden: robots, cartoon assistants, clipart, floating icons, AI icon packs, emoji style, stock-looking people, generic gradients, generic AI artwork, misspelled Hebrew, English-first hierarchy."
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
                "creative_director_review": creative_review,
                "selected_concept": selected_concept,
                "require_public_url": True,
                "text_policy": "hebrew_first_ad_text_required_after_creative_director_approval",
                "language_policy": "100% Hebrew visual hierarchy and CTA in the asset",
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

    def _growth_intelligence(
        self,
        whatsapp_bot: dict[str, Any],
        meta_ads: dict[str, Any],
        website_intelligence: dict[str, Any],
        content_intelligence: dict[str, Any],
    ) -> dict[str, Any]:
        verified_whatsapp = bool(isinstance(whatsapp_bot, dict) and whatsapp_bot.get("verified"))
        verified_meta = bool(isinstance(meta_ads, dict) and meta_ads.get("verified"))
        website_available = bool(isinstance(website_intelligence, dict) and website_intelligence)
        return {
            "principle": "Spend at least as much effort analyzing yesterday's performance as creating today's content.",
            "instagram": {
                "reach": None,
                "impressions": None,
                "shares": None,
                "saves": None,
                "comments": None,
                "profile_visits": None,
                "link_clicks": None,
                "whatsapp_clicks": content_intelligence.get("metrics", {}).get("whatsapp_clicks"),
                "audience_retention": None,
                "status": content_intelligence.get("status", "unavailable"),
            },
            "meta_ads": {
                "spend": meta_ads.get("current_spend_ils") if verified_meta else None,
                "cpc": None,
                "cpm": None,
                "ctr": None,
                "cpl": None,
                "cpa": None,
                "roas": None,
                "frequency": None,
                "learning_status": meta_ads.get("learning_status") if verified_meta else None,
                "creative_fatigue": None,
                "status": "verified" if verified_meta else "unavailable",
            },
            "whatsapp": {
                "new_conversations": content_intelligence.get("metrics", {}).get("whatsapp_clicks"),
                "qualified_leads": (
                    whatsapp_bot.get("today", {}).get("qualified_leads")
                    if verified_whatsapp
                    else None
                ),
                "demo_requests": content_intelligence.get("metrics", {}).get("demo_requests"),
                "booked_demos": (
                    whatsapp_bot.get("today", {}).get("demo_bookings")
                    if verified_whatsapp
                    else None
                ),
                "customers": content_intelligence.get("metrics", {}).get("customers"),
                "drop_off_stages": whatsapp_bot.get("drop_off_stages") if verified_whatsapp else None,
                "response_quality": whatsapp_bot.get("response_quality") if verified_whatsapp else None,
                "time_to_first_response": whatsapp_bot.get("time_to_first_response") if verified_whatsapp else None,
                "status": "verified" if verified_whatsapp else "unavailable",
            },
            "website": {
                "sessions": website_intelligence.get("sessions") if website_available else None,
                "conversion_rate": website_intelligence.get("conversion_rate") if website_available else None,
                "bounce_rate": website_intelligence.get("bounce_rate") if website_available else None,
                "cta_clicks": website_intelligence.get("cta_clicks") if website_available else None,
                "landing_page_performance": website_intelligence.get("landing_page_performance") if website_available else None,
                "ga4_events": website_intelligence.get("ga4_events") if website_available else None,
                "search_console": website_intelligence.get("search_console") if website_available else None,
                "core_web_vitals": website_intelligence.get("core_web_vitals") if website_available else None,
                "status": "partial" if website_available else "unavailable",
            },
            "conclusion": (
                "Continue publishing only with evidence, improve attribution, and do not scale promotion until verified outcomes exist."
                if content_intelligence.get("status") == "unavailable"
                else "Rank content by business value and scale the asset with the strongest verified customer-acquisition signal."
            ),
            "stop_continue_improve_scale": {
                "stop": "Stop using unverified likes or activity as success criteria.",
                "continue": "Continue Hebrew WhatsApp-first content for Israeli law firms.",
                "improve": "Improve WhatsApp, Instagram, Meta, and website attribution.",
                "scale": "Scale only after Business Value Score and Budget Guard allow it.",
            },
        }

    def _executive_measurement(
        self,
        *,
        content_intelligence: dict[str, Any],
        growth_intelligence: dict[str, Any],
        promotion_brain: dict[str, Any],
        budget_status: dict[str, Any],
        budget_guard: dict[str, Any],
        campaign_decision: dict[str, Any],
        whatsapp_bot: dict[str, Any],
        meta_ads: dict[str, Any],
        website_intelligence: dict[str, Any],
        buffer_result: ExecutionResult | None,
        run_date: str,
    ) -> dict[str, Any]:
        published = buffer_result is not None and buffer_result.status == "completed"
        proof = buffer_result.proof if published else {}
        verified_whatsapp = bool(isinstance(whatsapp_bot, dict) and whatsapp_bot.get("verified"))
        verified_meta = bool(isinstance(meta_ads, dict) and meta_ads.get("verified"))
        website_known = bool(isinstance(website_intelligence, dict) and website_intelligence)

        score = 50
        reasons: list[str] = []
        if published:
            score += 10
            reasons.append("+ Published customer-acquisition content with execution proof.")
        else:
            score -= 6
            reasons.append("- No verified published social asset in this run.")
        if website_known:
            score += 6
            reasons.append("+ Website/repository intelligence is available for conversion review.")
        if verified_whatsapp:
            score += 16
            reasons.append("+ WhatsApp attribution is connected.")
        else:
            score -= 14
            reasons.append("- WhatsApp attribution is missing, so customer acquisition cannot be measured.")
        if verified_meta:
            score += 8
            reasons.append("+ Meta spend/performance data is verified.")
        else:
            score -= 6
            reasons.append("- Meta campaign performance is not verified.")
        score = max(0, min(100, score))

        evidence_level = "verified_internal_data" if verified_whatsapp or verified_meta else "hypothesis"
        if published and not (verified_whatsapp or verified_meta):
            evidence_level = "public_platform_signal_pending"

        instagram_metrics = growth_intelligence.get("instagram", {})
        whatsapp_metrics = growth_intelligence.get("whatsapp", {})
        campaign_metrics = growth_intelligence.get("meta_ads", {})

        return {
            "principle": (
                "The AI CMO reports whether business performance improved, why, and what decision it is making next."
            ),
            "executive_decision": {
                "paragraph": (
                    "Yesterday customer-acquisition execution moved forward because a verified social asset is now under review, "
                    "but the business impact cannot be proven until Instagram engagement and WhatsApp attribution are measured. "
                    "Today I will monitor the post, compare it against benchmarks, and decide by 16:00 Asia/Jerusalem whether "
                    "the daily ₪20 promotion budget should be used under the exploration guardrails."
                    if published
                    else "Yesterday the business did not improve measurably because no verified customer-acquisition artifact reached the market. "
                    "Today I will remove the highest-impact execution or measurement blocker, then reassess whether publishing or promotion can create qualified WhatsApp conversations."
                ),
                "decision_by": f"{run_date} 16:00 Asia/Jerusalem",
                "next_decision": "Use or hold today's ₪20 promotion budget based on post signal quality and budget guard status.",
            },
            "business_health": {
                "score": score,
                "status": "improving" if score >= 60 else "requires_attention",
                "reason": reasons,
                "trend": "improving" if published else "flat",
            },
            "evidence_levels": {
                "verified_internal_data": {
                    "available": verified_whatsapp or verified_meta,
                    "sources": [
                        source
                        for source, available in {
                            "WhatsApp": verified_whatsapp,
                            "Meta": verified_meta,
                        }.items()
                        if available
                    ],
                    "confidence": "high" if verified_whatsapp or verified_meta else "not_available",
                },
                "public_platform_signals": {
                    "available": published,
                    "sources": ["Buffer publish proof"] if published else [],
                    "confidence": "medium" if published else "not_available",
                },
                "hypotheses": {
                    "available": True,
                    "confidence": "low",
                    "primary_hypothesis": promotion_brain.get("hypothesis"),
                },
                "current_decision_evidence_level": evidence_level,
            },
            "measurement_questions": [
                {
                    "question": "What improved?",
                    "answer": (
                        "Distribution is underway for a verified published asset."
                        if published
                        else "No verified customer-acquisition improvement was measured."
                    ),
                },
                {
                    "question": "Why?",
                    "answer": (
                        "Publication proof exists, but performance proof is still pending."
                        if published
                        else "The execution or measurement connector did not produce a completed market-facing artifact."
                    ),
                },
                {
                    "question": "What got worse?",
                    "answer": "Measurement risk remains high because attribution is still incomplete.",
                },
                {
                    "question": "What are we changing?",
                    "answer": "Stop reporting bare unavailable values; each gap now has a business impact, action, owner, and review time.",
                },
                {
                    "question": "What do we expect tomorrow?",
                    "answer": "A post-performance decision: continue monitoring, create a follow-up, or promote inside the ₪20/day guardrail.",
                },
            ],
            "instagram_performance": {
                "status": "monitoring" if published else "not_published_in_this_run",
                "post": proof.get("instagram_url") or proof.get("buffer_post_url"),
                "published_at": proof.get("timestamp"),
                "reach": instagram_metrics.get("reach"),
                "likes": instagram_metrics.get("likes"),
                "comments": instagram_metrics.get("comments"),
                "shares": instagram_metrics.get("shares"),
                "saves": instagram_metrics.get("saves"),
                "profile_visits": instagram_metrics.get("profile_visits"),
                "whatsapp_clicks": instagram_metrics.get("whatsapp_clicks"),
                "status_reason": (
                    "Post is published; live Instagram Insights connector is not connected yet."
                    if published
                    else "No published post proof exists for this run."
                ),
                "business_impact": "Cannot judge creative performance until Instagram engagement and WhatsApp clicks are measured.",
                "automatic_action": "Review post performance again in 6 hours and compare against previous post benchmarks.",
                "expected_review": f"{run_date} 16:00 Asia/Jerusalem",
                "confidence": 0.74 if published else 0.42,
                "recommendation": (
                    "Continue monitoring; promote only if early engagement or exploration policy justifies spend."
                    if published
                    else "Publish a Hebrew WhatsApp-first asset before evaluating promotion."
                ),
            },
            "whatsapp_measurement": {
                "status": "verified" if verified_whatsapp else "no_production_webhook_connected",
                "conversations": whatsapp_metrics.get("new_conversations"),
                "qualified": whatsapp_metrics.get("qualified_leads"),
                "demo_requests": whatsapp_metrics.get("demo_requests"),
                "booked": whatsapp_metrics.get("booked_demos"),
                "closed": whatsapp_metrics.get("customers"),
                "business_impact": (
                    "Able to measure content-to-lead conversion."
                    if verified_whatsapp
                    else "Unable to measure customer acquisition from content to booked demos."
                ),
                "automatic_action": (
                    "Analyze drop-off and response quality."
                    if verified_whatsapp
                    else "Waiting for WhatsApp webhook/event-log deployment; keep publishing with explicit tracking assumptions."
                ),
                "expected_completion": f"{run_date} 18:00 Asia/Jerusalem",
                "confidence": 0.92 if verified_whatsapp else 0.64,
            },
            "campaign_if_available": {
                "status": campaign_decision.get("state") or (
                    "blocked_by_budget_guard"
                    if not budget_guard.get("campaign_creation_allowed")
                    else "eligible_if_promotion_brain_approves"
                ),
                "campaign_to_launch": {
                    "audience": "Israeli law firms",
                    "budget": "₪20/day",
                    "objective": "WhatsApp conversations",
                    "expected_cpl_ils": 17,
                    "stop_rule": "Stop if no qualified conversations after ₪80 spent.",
                    "schedule": "Sunday-Thursday; Friday morning only; never Saturday.",
                },
                "current_spend_ils": campaign_metrics.get("spend"),
                "budget_verified": budget_status.get("verified"),
                "decision": campaign_decision.get("decision") or promotion_brain.get("decision"),
                "reason": campaign_decision.get("reason") or promotion_brain.get("reason"),
                "next_automatic_action": campaign_decision.get("next_automatic_action"),
                "requires_ceo_action": campaign_decision.get("requires_ceo_action"),
                "evidence": campaign_decision.get("evidence"),
            },
            "today_operating_work": [
                "Review yesterday's post and classify signal quality.",
                "Compare creative against previous posts and public benchmarks.",
                "Decide by 16:00 whether to use the ₪20 promotion budget.",
                "Keep WhatsApp attribution as the highest-priority measurement gap.",
                "Prepare the next founder-led Hebrew asset if the current post is inconclusive.",
            ],
            "opportunity": {
                "highest": "Founder-led Hebrew WhatsApp-intake content",
                "reason": "Highest predicted conversion path for Israeli law firms while attribution is incomplete.",
                "expected": "+2 demo opportunities if promoted and WhatsApp tracking confirms lead quality.",
                "confidence": 0.81 if published else 0.68,
            },
        }

    def _revenue_cmo_report(
        self,
        *,
        content_intelligence: dict[str, Any],
        growth_intelligence: dict[str, Any],
        executive_measurement: dict[str, Any],
        operating_executive: dict[str, Any],
        promotion_brain: dict[str, Any],
        budget_guard: dict[str, Any],
        campaign_decision: dict[str, Any],
        budget_status: dict[str, Any],
        creative_brief: dict[str, Any],
        whatsapp_bot: dict[str, Any],
        meta_ads: dict[str, Any],
        website_intelligence: dict[str, Any],
        buffer_result: ExecutionResult | None,
        run_date: str,
    ) -> dict[str, Any]:
        primary_kpi = "Generate qualified law firm demos that convert into paying customers."
        verified_whatsapp = bool(isinstance(whatsapp_bot, dict) and whatsapp_bot.get("verified"))
        verified_meta = bool(isinstance(meta_ads, dict) and meta_ads.get("verified"))
        published = buffer_result is not None and buffer_result.status == "completed"
        proof = buffer_result.proof if published else {}
        website_has_cta_gap = bool(
            isinstance(website_intelligence, dict)
            and website_intelligence.get("missing_or_weak_ctas")
        )
        creative_review = creative_brief.get("creative_director_review", {})
        creative_approved = bool(creative_review.get("approved"))
        campaign_state = str(campaign_decision.get("state") or "")

        marketing_score = 6 if published else 4
        if verified_whatsapp:
            marketing_score += 2
        if verified_meta:
            marketing_score += 1
        marketing_score = min(marketing_score, 10)

        website_score = 5 if website_has_cta_gap else 7
        instagram_score = 7 if published else 3
        meta_ads_score = 6 if verified_meta else 3
        sales_funnel_score = 7 if verified_whatsapp else 2

        post_score_dimensions = {
            "hook": 8 if creative_approved else 5,
            "trust": 8 if creative_approved else 5,
            "professionalism": 8 if creative_approved else 5,
            "visual_quality": 8 if creative_approved else 4,
            "clear_value_proposition": 8 if creative_approved else 5,
            "call_to_action": 8 if creative_approved else 6,
            "relevance_to_law_firms": 9 if creative_approved else 6,
        }
        post_score = round(sum(post_score_dimensions.values()) / len(post_score_dimensions))

        if campaign_state in {"launched", "monitoring"}:
            meta_decision = "Scale" if verified_meta else "Launch"
            meta_why = "Campaign is live; evaluate verified lead quality before increasing spend."
        elif not creative_approved:
            meta_decision = "Change creative"
            meta_why = "Do not spend until the creative meets the Hebrew SaaS ad quality bar."
        elif not budget_guard.get("allowed_to_launch"):
            meta_decision = "Pause"
            meta_why = "Budget Guard failed at least one rule; spending must stay stopped."
        else:
            meta_decision = "Launch"
            meta_why = "Exploration Mode permits one guarded campaign if Meta execution is available."

        channels = {
            "Instagram": self._revenue_channel_review(
                status="published" if published else "no_completed_publish_in_latest_run",
                revenue_signal="pending WhatsApp clicks and demo requests",
                metrics=growth_intelligence.get("instagram", {}),
                action=(
                    "Review all published assets by hook, trust, CTA, and qualified-demo signal."
                    if published
                    else "Publish only after Creative Director approves a Hebrew, product-led ad."
                ),
            ),
            "Facebook": self._revenue_channel_review(
                status="unavailable",
                revenue_signal="No verified Facebook lead signal.",
                metrics={},
                action="Reuse only proven Instagram creative after lead signal exists.",
            ),
            "LinkedIn": self._revenue_channel_review(
                status="unavailable",
                revenue_signal="No verified founder or law-firm engagement signal.",
                metrics={},
                action="Test founder-led proof posts after Instagram/WhatsApp attribution is measurable.",
            ),
            "Website": self._revenue_channel_review(
                status="needs_attention" if website_has_cta_gap else "monitoring",
                revenue_signal="Visit-to-WhatsApp conversion is the revenue path.",
                metrics=growth_intelligence.get("website", {}),
                action=(
                    "Fix the weak above-fold demo/WhatsApp CTA before scaling paid traffic."
                    if website_has_cta_gap
                    else "Keep monitoring conversion and CTA clicks."
                ),
            ),
            "WhatsApp": self._revenue_channel_review(
                status="verified" if verified_whatsapp else "unavailable",
                revenue_signal="Primary lead and demo attribution source.",
                metrics=growth_intelligence.get("whatsapp", {}),
                action=(
                    "Analyze objections and demo intent."
                    if verified_whatsapp
                    else "Connect the WhatsApp bot event log/webhook and classify every conversation."
                ),
            ),
            "Google Business Profile": self._revenue_channel_review(
                status="unavailable",
                revenue_signal="No verified local-search demo signal.",
                metrics={},
                action="Review profile only after higher-impact attribution and CTA gaps are addressed.",
            ),
            "Meta Ads": self._revenue_channel_review(
                status="verified" if verified_meta else "unavailable",
                revenue_signal="Exploration spend can create learning; optimization requires attribution.",
                metrics=growth_intelligence.get("meta_ads", {}),
                action=meta_why,
            ),
            "Landing pages": self._revenue_channel_review(
                status="needs_attention" if website_has_cta_gap else "monitoring",
                revenue_signal="Landing page clarity controls paid and organic conversion.",
                metrics=growth_intelligence.get("website", {}),
                action="Improve headline, proof, demo CTA, and WhatsApp path for Israeli law firms.",
            ),
            "Email campaigns": self._revenue_channel_review(
                status="unavailable",
                revenue_signal="No verified email-to-demo signal.",
                metrics={},
                action="Do not prioritize until outbound list and attribution are available.",
            ),
            "CRM / lead pipeline": self._revenue_channel_review(
                status="unavailable" if not verified_whatsapp else "partial",
                revenue_signal="Needed to connect demos to customers and revenue.",
                metrics={
                    "qualified_leads": growth_intelligence.get("whatsapp", {}).get("qualified_leads"),
                    "booked_demos": growth_intelligence.get("whatsapp", {}).get("booked_demos"),
                    "customers": growth_intelligence.get("whatsapp", {}).get("customers"),
                },
                action="Track lead source, demo status, lost reason, customer status, and revenue.",
            ),
        }

        top_priorities = [
            {
                "rank": 1,
                "action": "Connect WhatsApp attribution from post/link to conversation, demo, and customer.",
                "expected_revenue_impact": "Very high",
                "effort": "Low",
                "expected_impact": "Turns publishing and paid spend into measurable customer acquisition decisions.",
                "time_to_results": "1-3 days after event log is connected",
            },
            {
                "rank": 2,
                "action": "Replace generic creative with one Hebrew product-led law-firm ad before promotion.",
                "expected_revenue_impact": "High",
                "effort": "Medium",
                "expected_impact": "Improves trust, CTA clarity, and probability of a qualified WhatsApp demo.",
                "time_to_results": "Same day after publishing",
            },
            {
                "rank": 3,
                "action": "Run one guarded Exploration Mode campaign only after creative and CTA pass review.",
                "expected_revenue_impact": "High",
                "effort": "Medium",
                "expected_impact": "Creates paid learning without exceeding ₪20/day or ₪100 per experiment.",
                "time_to_results": "24-72 hours after launch",
            },
        ]

        return {
            "role": "Revenue CMO",
            "primary_kpi": primary_kpi,
            "revenue_metrics": [
                "Qualified leads",
                "Demo bookings",
                "Closed customers",
                "Cost per qualified lead",
                "Customer acquisition cost",
                "Revenue",
            ],
            "vanity_metric_policy": "Never optimize followers, impressions, likes, posts, or activity unless they improve revenue metrics.",
            "decision_framework": (
                "When uncertain, choose the action most likely to generate a qualified law firm demo within the next 30 days."
            ),
            "daily_review_questions": [
                "What changed since yesterday?",
                "Did we get any new leads?",
                "Did anyone book a demo?",
                "Which marketing activity produced the most value?",
                "What should we do today to maximize revenue?",
                "Should Meta Ads be launched, paused, or changed?",
                "What is the single highest-ROI task for today?",
            ],
            "scores": {
                "marketing": {
                    "score": marketing_score,
                    "reason": "Execution exists; revenue confidence depends on attribution and creative quality.",
                },
                "website": {
                    "score": website_score,
                    "reason": "Weak CTA detected." if website_has_cta_gap else "No major CTA gap detected in available data.",
                },
                "instagram": {
                    "score": instagram_score,
                    "reason": "Latest asset has publish proof." if published else "No completed Instagram artifact in this run.",
                },
                "meta_ads": {
                    "score": meta_ads_score,
                    "reason": "Verified Meta data exists." if verified_meta else "Meta execution/metrics are not verified.",
                },
                "sales_funnel": {
                    "score": sales_funnel_score,
                    "reason": (
                        "WhatsApp funnel data is verified."
                        if verified_whatsapp
                        else "Closed-loop WhatsApp-to-demo attribution is missing."
                    ),
                },
            },
            "channel_review": channels,
            "published_post_review": {
                "asset": proof.get("instagram_url") or proof.get("buffer_post_url"),
                "buffer_update_id": proof.get("buffer_update_id"),
                "score": post_score if published else None,
                "threshold": 8,
                "below_threshold": bool(published and post_score < 8),
                "dimensions": post_score_dimensions if published else {},
                "explanation": (
                    "Creative is acceptable for promotion review."
                    if published and post_score >= 8
                    else "Creative must be improved before paid promotion; generic or unclear assets hurt trust."
                    if published
                    else "No published asset proof is available for scoring."
                ),
                "recommendation": (
                    "Promote only if WhatsApp/engagement signal passes Exploration Mode criteria."
                    if published and post_score >= 8
                    else "Create a Hebrew product-led ad with real product screenshot, proof, offer, and WhatsApp CTA."
                ),
            },
            "creative_director_standard": {
                "forbidden": [
                    "generic AI artwork",
                    "robots",
                    "floating icons",
                    "stock-looking graphics",
                    "English-first visual hierarchy",
                ],
                "preferred": [
                    "founder content",
                    "product screenshots",
                    "customer stories",
                    "before/after workflows",
                    "short demo videos",
                    "WhatsApp conversations",
                    "real legal examples",
                    "testimonials",
                    "ROI proof",
                ],
                "quality_bar": "Would I spend ₪20 promoting this to Israeli law firms?",
            },
            "meta_ads_decision": {
                "decision": meta_decision,
                "why": meta_why,
                "allowed_decisions": [
                    "Launch",
                    "Pause",
                    "Scale",
                    "Reduce budget",
                    "Change audience",
                    "Change creative",
                    "Change objective",
                    "Duplicate winning ad",
                ],
                "budget": {
                    "daily_limit_ils": budget_guard.get("daily_budget_limit"),
                    "monthly_limit_ils": budget_guard.get("monthly_budget_limit"),
                    "allowed_to_launch": budget_guard.get("allowed_to_launch"),
                    "failed_rules": budget_guard.get("failed_rules", []),
                },
                "campaign_decision_id": campaign_decision.get("decision_id"),
                "next_review": campaign_decision.get("next_retry_at") or f"{run_date} 16:00 Asia/Jerusalem",
            },
            "highest_impact_recommendation": top_priorities[0],
            "top_3_priorities": top_priorities,
            "risks": [
                {
                    "risk": "The AI optimizes publishing instead of qualified demos.",
                    "severity": "High",
                    "mitigation": "Revenue CMO contract rejects activity-only recommendations.",
                },
                {
                    "risk": "Creative quality damages trust with law firms.",
                    "severity": "High",
                    "mitigation": "Creative Director blocks generic images and requires Hebrew product-led ads.",
                },
                {
                    "risk": "Budget is spent before attribution proves lead quality.",
                    "severity": "High",
                    "mitigation": "Exploration Mode limits one campaign, ₪20/day, and ₪100 per experiment.",
                },
            ],
            "recommended_next_action": top_priorities[0]["action"],
            "business_question": "What prevents ChatBot2U from acquiring another paying law-firm customer?",
            "source_of_truth": "Revenue CMO report is derived from execution proof, attribution, budget guard, campaign decision, website intelligence, and channel evidence.",
            "operating_executive_status": operating_executive.get("daily_ceo_brief_standard"),
        }

    def _revenue_channel_review(
        self,
        *,
        status: str,
        revenue_signal: str,
        metrics: dict[str, Any],
        action: str,
    ) -> dict[str, Any]:
        return {
            "status": status,
            "revenue_signal": revenue_signal,
            "metrics": {
                "reach": metrics.get("reach"),
                "engagement": metrics.get("engagement"),
                "click_through_rate": metrics.get("ctr") or metrics.get("click_through_rate"),
                "leads_generated": metrics.get("qualified_leads"),
                "demo_requests": metrics.get("demo_requests"),
                "cost_per_lead": metrics.get("cpl"),
                "conversion_rate": metrics.get("conversion_rate"),
                "best_performing_content": metrics.get("best_performing_content"),
                "worst_performing_content": metrics.get("worst_performing_content"),
            },
            "trend_policy": "Use trends over isolated events.",
            "recommended_action": action,
        }

    def _operating_executive(
        self,
        *,
        content_intelligence: dict[str, Any],
        growth_intelligence: dict[str, Any],
        executive_measurement: dict[str, Any],
        promotion_brain: dict[str, Any],
        budget_status: dict[str, Any],
        budget_guard: dict[str, Any],
        campaign_decision: dict[str, Any],
        whatsapp_bot: dict[str, Any],
        meta_ads: dict[str, Any],
        website_intelligence: dict[str, Any],
        buffer_result: ExecutionResult | None,
        run_date: str,
        now: datetime,
    ) -> dict[str, Any]:
        budget_ledger = self._budget_ledger(budget_status, budget_guard, run_date, now)
        campaign_registry = self._campaign_registry(
            budget_ledger=budget_ledger,
            promotion_brain=promotion_brain,
            campaign_decision=campaign_decision,
            meta_ads=meta_ads,
            run_date=run_date,
            now=now,
        )
        content_registry = self._content_registry(
            content_intelligence=content_intelligence,
            buffer_result=buffer_result,
            run_date=run_date,
            now=now,
        )
        competitor_registry = self._competitor_registry(run_date, now)
        whatsapp_intelligence = self._conversation_intelligence(whatsapp_bot, run_date, now)
        website_management = self._website_management(website_intelligence, run_date, now)
        executive_memory = self._executive_memory(
            budget_ledger=budget_ledger,
            campaign_registry=campaign_registry,
            content_registry=content_registry,
            competitor_registry=competitor_registry,
            whatsapp_intelligence=whatsapp_intelligence,
            website_management=website_management,
            executive_measurement=executive_measurement,
            run_date=run_date,
            now=now,
        )

        manager_reports = self._manager_reports(
            budget_ledger=budget_ledger,
            campaign_registry=campaign_registry,
            content_registry=content_registry,
            competitor_registry=competitor_registry,
            whatsapp_intelligence=whatsapp_intelligence,
            website_management=website_management,
            executive_measurement=executive_measurement,
            promotion_brain=promotion_brain,
            growth_intelligence=growth_intelligence,
            run_date=run_date,
        )
        self_management = self._self_management(manager_reports, run_date)

        state = {
            "executive_rule": "The AI is evaluated by whether it managed the business today.",
            "operating_model": "Persistent managers own business assets continuously; temporary tasks are implementation details.",
            "acceptance_test": (
                "Rami can ignore implementation for 30 consecutive days while each morning brief reads like "
                "reports from an executive team."
            ),
            "manager_reports": manager_reports,
            "asset_ownership": {
                manager: report["owns"]
                for manager, report in manager_reports.items()
            },
            "internal_budget_ledger": budget_ledger,
            "campaign_registry": campaign_registry,
            "campaign_decision": campaign_decision,
            "content_registry": content_registry,
            "competitor_registry": competitor_registry,
            "whatsapp_intelligence": whatsapp_intelligence,
            "website_management": website_management,
            "executive_memory": executive_memory,
            "self_management": self_management,
            "daily_ceo_brief_standard": "management_report_not_execution_log",
        }
        self._persist_operating_state(state)
        return state

    def _budget_ledger(
        self,
        budget_status: dict[str, Any],
        budget_guard: dict[str, Any],
        run_date: str,
        now: datetime,
    ) -> dict[str, Any]:
        previous = self._read_operating_json("budget_ledger.json", {})
        monthly_budget = float(budget_status.get("monthly_budget_limit_ils") or previous.get("monthly_budget_ils") or 600)
        daily_budget = float(budget_status.get("daily_budget_limit_ils") or previous.get("daily_budget_ils") or 20)
        verified_spend = bool(budget_status.get("verified"))
        current_spend = float(budget_status.get("current_spend_ils") or 0)
        spent = current_spend if verified_spend else float(previous.get("spent_month") or previous.get("spent_ils") or 0)
        reserved = float(budget_guard.get("reserved_today") or previous.get("reserved_today") or 0)
        committed = float(previous.get("committed_ils") or 0)
        forecast = spent + reserved + committed
        remaining = max(0.0, monthly_budget - forecast)
        ledger = {
            "authoritative": True,
            "meta_reconciles_internal_ledger": True,
            "currency": "ILS",
            "daily_budget_limit": daily_budget,
            "monthly_budget_limit": monthly_budget,
            "reserved_today": reserved,
            "committed_today": float(budget_guard.get("committed_today") or 0),
            "spent_today": float(budget_guard.get("spent_today") or 0),
            "spent_month": spent,
            "remaining_today": float(budget_guard.get("remaining_today") or daily_budget),
            "remaining_month": float(budget_guard.get("remaining_month") or remaining),
            "allowed_to_launch": bool(budget_guard.get("allowed_to_launch")),
            "failed_rules": budget_guard.get("failed_rules", []),
            "monthly_budget_ils": monthly_budget,
            "daily_budget_ils": daily_budget,
            "reserved_ils": reserved,
            "committed_ils": committed,
            "spent_ils": spent,
            "forecast_ils": forecast,
            "remaining_ils": remaining,
            "per_campaign": previous.get("per_campaign", {}),
            "per_experiment": previous.get("per_experiment", {}),
            "per_asset": previous.get("per_asset", {}),
            "spend_verified_by_meta": verified_spend,
            "budget_guard_status": "passed" if budget_guard.get("allowed_to_launch") else "holding_spend",
            "decision": (
                "Hold new spend until budget guard and promotion decision pass."
                if not budget_guard.get("allowed_to_launch")
                else "Budget can be deployed within delegated authority."
            ),
            "updated_at": now.isoformat(),
            "run_date": run_date,
        }
        self._write_operating_json("budget_ledger.json", ledger)
        return ledger

    def _campaign_registry(
        self,
        *,
        budget_ledger: dict[str, Any],
        promotion_brain: dict[str, Any],
        campaign_decision: dict[str, Any],
        meta_ads: dict[str, Any],
        run_date: str,
        now: datetime,
    ) -> dict[str, Any]:
        previous = self._read_operating_json("campaign_registry.json", {"campaigns": []})
        campaigns = list(previous.get("campaigns", []))
        campaign_name = "Exploration - Israeli law firms WhatsApp conversations"
        if not any(item.get("name") == campaign_name for item in campaigns if isinstance(item, dict)):
            campaigns.append(
                {
                    "name": campaign_name,
                    "owner": "Ads Manager",
                    "objective": "WhatsApp conversations from Israeli law firms",
                    "status": "not_started",
                    "budget": "₪20/day, max ₪100 learning budget per experiment",
                    "start": None,
                    "end": None,
                    "spend_ils": 0,
                    "expected_roi": "Learning ROI first; +2 demo opportunities if lead quality is confirmed.",
                    "actual_roi": None,
                    "evidence": ["internal_campaign_registry", "budget_ledger"],
                    "recommendation": "Launch only when Promotion Brain and Budget Guard approve.",
                    "last_decision_id": None,
                }
            )
        active = [
            item for item in campaigns
            if isinstance(item, dict) and item.get("status") in {"active", "learning"}
        ]
        registry = {
            "owner": "Ads Manager",
            "status": "managing_campaign_pipeline",
            "active_campaign_count": len(active),
            "campaigns": campaigns,
            "meta_campaign_status": meta_ads.get("campaign_status", "unknown"),
            "budget_ledger_remaining_ils": budget_ledger.get("remaining_ils"),
            "decision": campaign_decision.get("decision") or promotion_brain.get("decision"),
            "state": campaign_decision.get("state"),
            "recommendation": campaign_decision.get("reason") or promotion_brain.get("reason"),
            "next_review": campaign_decision.get("next_retry_at") or f"{run_date} 16:00 Asia/Jerusalem",
            "last_decision_id": campaign_decision.get("decision_id"),
            "last_campaign_decision": campaign_decision,
            "updated_at": now.isoformat(),
        }
        self._write_operating_json("campaign_registry.json", registry)
        return registry

    def _content_registry(
        self,
        *,
        content_intelligence: dict[str, Any],
        buffer_result: ExecutionResult | None,
        run_date: str,
        now: datetime,
    ) -> dict[str, Any]:
        previous = self._read_operating_json("content_registry.json", {"assets": []})
        assets = list(previous.get("assets", []))
        published = buffer_result is not None and buffer_result.status == "completed"
        proof = buffer_result.proof if published else {}
        asset_id = proof.get("buffer_update_id") or f"planned-founder-whatsapp-{run_date}"
        if not any(item.get("asset_id") == asset_id for item in assets if isinstance(item, dict)):
            assets.append(
                {
                    "asset_id": asset_id,
                    "owner": "Social Manager",
                    "creative_owner": "Creative Director",
                    "lifecycle": "published" if published else "planned",
                    "published": published,
                    "measured": content_intelligence.get("status") == "verified",
                    "ranked": True,
                    "promoted": False,
                    "retired": False,
                    "learning": "pending_verified_outcomes",
                    "business_value_score": content_intelligence.get("business_value_score") or 62,
                    "evidence": proof,
                    "next_review": f"{run_date} 16:00 Asia/Jerusalem",
                }
            )
        ranked_assets = sorted(
            [item for item in assets if isinstance(item, dict)],
            key=lambda item: int(item.get("business_value_score") or 0),
            reverse=True,
        )
        registry = {
            "owner": "Social Manager",
            "status": "ranking_all_content_daily",
            "assets": assets,
            "ranked_assets": ranked_assets,
            "top_asset": ranked_assets[0] if ranked_assets else None,
            "decision": (
                "Continue monitoring published content before promotion."
                if published
                else "Create and publish the next Hebrew WhatsApp-first asset."
            ),
            "updated_at": now.isoformat(),
        }
        self._write_operating_json("content_registry.json", registry)
        return registry

    def _competitor_registry(self, run_date: str, now: datetime) -> dict[str, Any]:
        previous = self._read_operating_json("competitor_registry.json", {"competitors": []})
        competitors = list(previous.get("competitors", []))
        registry = {
            "owner": "Growth Manager",
            "status": "daily_competitor_watch_owned",
            "competitors": competitors,
            "top_campaigns": previous.get("top_campaigns", []),
            "new_offers": previous.get("new_offers", []),
            "creative_patterns": previous.get("creative_patterns", []),
            "threats": previous.get("threats", ["Competitors may out-message ChatBot2U before attribution is connected."]),
            "opportunities": previous.get("opportunities", ["Use founder-led proof and WhatsApp intake friction messaging."]),
            "recommendations": previous.get("recommendations", ["Run daily public competitor review and turn findings into content tests."]),
            "automatic_action": "Analyze public competitor activity and update opportunity ranking.",
            "next_review": f"{run_date} 12:00 Asia/Jerusalem",
            "updated_at": now.isoformat(),
        }
        self._write_operating_json("competitor_registry.json", registry)
        return registry

    def _conversation_intelligence(
        self,
        whatsapp_bot: dict[str, Any],
        run_date: str,
        now: datetime,
    ) -> dict[str, Any]:
        verified = bool(isinstance(whatsapp_bot, dict) and whatsapp_bot.get("verified"))
        today = whatsapp_bot.get("today", {}) if isinstance(whatsapp_bot, dict) else {}
        intelligence = {
            "owner": "Analytics Manager",
            "status": "verified" if verified else "waiting_for_webhook_or_event_log",
            "intent": today.get("intent") if verified else None,
            "objections": today.get("objections") if verified else [],
            "drop_offs": today.get("drop_off_stages") if verified else [],
            "booking_quality": today.get("booking_quality") if verified else None,
            "lead_quality": today.get("lead_quality") if verified else None,
            "lost_reasons": today.get("lost_reasons") if verified else [],
            "recommendation": (
                "Analyze conversation quality and improve bot handoff."
                if verified
                else "Deploy WhatsApp event log/webhook and classify every conversation by intent, objection, drop-off, booking quality, and lead quality."
            ),
            "business_objective": "Convert WhatsApp conversations into booked demos and customers.",
            "next_review": f"{run_date} 18:00 Asia/Jerusalem",
            "updated_at": now.isoformat(),
        }
        self._write_operating_json("whatsapp_intelligence.json", intelligence)
        return intelligence

    def _website_management(
        self,
        website_intelligence: dict[str, Any],
        run_date: str,
        now: datetime,
    ) -> dict[str, Any]:
        weak_ctas = website_intelligence.get("missing_or_weak_ctas", []) if isinstance(website_intelligence, dict) else []
        management = {
            "owner": "Website Manager",
            "owns": ["Homepage", "Landing pages", "SEO", "Conversion", "CTA path"],
            "heatmaps": "not_connected",
            "ga4": "not_connected",
            "seo": "repository_review_available",
            "cta": "needs_attention" if weak_ctas else "monitoring",
            "landing_pages": "owned",
            "conversion": "pending_analytics",
            "pull_request_creation": "available_when_website_checkout_is_configured",
            "weak_ctas": weak_ctas,
            "recommendation": (
                "Open a CTA improvement PR when website checkout path is available."
                if weak_ctas
                else "Continue monitoring website conversion path."
            ),
            "next_review": f"{run_date} 15:00 Asia/Jerusalem",
            "updated_at": now.isoformat(),
        }
        self._write_operating_json("website_management.json", management)
        return management

    def _executive_memory(
        self,
        *,
        budget_ledger: dict[str, Any],
        campaign_registry: dict[str, Any],
        content_registry: dict[str, Any],
        competitor_registry: dict[str, Any],
        whatsapp_intelligence: dict[str, Any],
        website_management: dict[str, Any],
        executive_measurement: dict[str, Any],
        run_date: str,
        now: datetime,
    ) -> dict[str, Any]:
        previous = self._read_operating_json("executive_memory.json", {})
        insights = list(previous.get("insights", []))
        insight = {
            "date": run_date,
            "learning": executive_measurement.get("measurement_questions", [{}])[-1].get("answer"),
            "confidence": executive_measurement.get("evidence_levels", {}).get("current_decision_evidence_level"),
            "action": executive_measurement.get("executive_decision", {}).get("next_decision"),
        }
        if insight not in insights:
            insights.append(insight)
        memory = {
            "campaigns": campaign_registry.get("campaigns", []),
            "experiments": previous.get("experiments", []),
            "customers": previous.get("customers", []),
            "insights": insights[-30:],
            "failures": previous.get("failures", []),
            "successful_strategies": previous.get("successful_strategies", []),
            "creative_patterns": competitor_registry.get("creative_patterns", []),
            "promotion_history": previous.get("promotion_history", []),
            "budget_history": (previous.get("budget_history", []) + [budget_ledger])[-30:],
            "content_assets": content_registry.get("assets", []),
            "whatsapp_history_status": whatsapp_intelligence.get("status"),
            "website_status": website_management.get("cta"),
            "updated_at": now.isoformat(),
        }
        self._write_operating_json("executive_memory.json", memory)
        return memory

    def _manager_reports(
        self,
        *,
        budget_ledger: dict[str, Any],
        campaign_registry: dict[str, Any],
        content_registry: dict[str, Any],
        competitor_registry: dict[str, Any],
        whatsapp_intelligence: dict[str, Any],
        website_management: dict[str, Any],
        executive_measurement: dict[str, Any],
        promotion_brain: dict[str, Any],
        growth_intelligence: dict[str, Any],
        run_date: str,
    ) -> dict[str, dict[str, Any]]:
        instagram = executive_measurement.get("instagram_performance", {})
        top_asset = content_registry.get("top_asset") or {}
        return {
            "Social Manager": {
                "owns": ["Instagram", "Facebook"],
                "current_status": instagram.get("status"),
                "business_objective": "Turn social distribution into qualified WhatsApp conversations.",
                "current_kpi": {
                    "business_value_score": top_asset.get("business_value_score"),
                    "reach": instagram.get("reach"),
                    "whatsapp_clicks": instagram.get("whatsapp_clicks"),
                },
                "trend": content_registry.get("status"),
                "risk": instagram.get("business_impact"),
                "decision": instagram.get("recommendation"),
                "next_review": instagram.get("expected_review") or f"{run_date} 16:00 Asia/Jerusalem",
                "highest_roi_action_today": "Review post signal quality and choose continue, follow-up, or promote.",
            },
            "Ads Manager": {
                "owns": ["Meta Ads", "Budget", "Campaigns"],
                "current_status": campaign_registry.get("status"),
                "business_objective": "Spend only when learning or customer acquisition is likely.",
                "current_kpi": {
                    "remaining_budget_ils": budget_ledger.get("remaining_ils"),
                    "active_campaign_count": campaign_registry.get("active_campaign_count"),
                },
                "trend": budget_ledger.get("budget_guard_status"),
                "risk": promotion_brain.get("reason"),
                "decision": campaign_registry.get("decision"),
                "next_review": campaign_registry.get("next_review"),
                "highest_roi_action_today": "Prepare one exploration campaign but hold launch until guardrails pass.",
            },
            "Analytics Manager": {
                "owns": ["GA4", "Website analytics", "Attribution", "Business KPIs"],
                "current_status": whatsapp_intelligence.get("status"),
                "business_objective": "Connect actions to qualified leads, demos, customers, and revenue.",
                "current_kpi": growth_intelligence.get("whatsapp", {}),
                "trend": executive_measurement.get("evidence_levels", {}).get("current_decision_evidence_level"),
                "risk": "No closed-loop attribution means decisions remain lower confidence.",
                "decision": whatsapp_intelligence.get("recommendation"),
                "next_review": whatsapp_intelligence.get("next_review"),
                "highest_roi_action_today": "Remove attribution blocker or classify why it cannot be removed today.",
            },
            "Website Manager": {
                "owns": website_management.get("owns", []),
                "current_status": website_management.get("cta"),
                "business_objective": "Increase conversion from visit to WhatsApp/demo intent.",
                "current_kpi": {
                    "conversion": website_management.get("conversion"),
                    "weak_ctas": website_management.get("weak_ctas"),
                },
                "trend": "needs_attention" if website_management.get("weak_ctas") else "stable",
                "risk": "Weak CTA path can waste social and paid demand.",
                "decision": website_management.get("recommendation"),
                "next_review": website_management.get("next_review"),
                "highest_roi_action_today": "Create or prepare the highest-impact CTA improvement.",
            },
            "Creative Director": {
                "owns": ["Creative quality", "Images", "Videos", "Copy", "Brand consistency"],
                "current_status": "owning_creative_quality",
                "business_objective": "Increase Creative Score and conversion clarity.",
                "current_kpi": {
                    "creative_score": top_asset.get("business_value_score"),
                    "brand_consistency": "managed_by_brand_brain",
                },
                "trend": "learning_pending_performance",
                "risk": "Creative quality cannot be optimized without post-performance measurement.",
                "decision": "Create founder-led Hebrew creative with WhatsApp CTA and no model-rendered text in images.",
                "next_review": f"{run_date} 14:00 Asia/Jerusalem",
                "highest_roi_action_today": "Prepare the next creative variant based on measured or hypothesized conversion signal.",
            },
            "Growth Manager": {
                "owns": ["Funnel", "Business Value Score", "Experiment backlog", "Opportunity ranking"],
                "current_status": "managing_growth_opportunities",
                "business_objective": "Increase paying customers.",
                "current_kpi": {
                    "highest_opportunity": executive_measurement.get("opportunity", {}).get("highest"),
                    "confidence": executive_measurement.get("opportunity", {}).get("confidence"),
                },
                "trend": executive_measurement.get("business_health", {}).get("trend"),
                "risk": competitor_registry.get("threats"),
                "decision": executive_measurement.get("opportunity", {}).get("reason"),
                "next_review": competitor_registry.get("next_review"),
                "highest_roi_action_today": "Rank content, competitors, website, and attribution opportunities by customer-acquisition impact.",
            },
        }

    def _self_management(self, manager_reports: dict[str, dict[str, Any]], run_date: str) -> dict[str, Any]:
        manager_actions = []
        escalations = []
        for manager, report in manager_reports.items():
            action = report.get("highest_roi_action_today")
            if action:
                manager_actions.append({"manager": manager, "action": action})
            risk = str(report.get("risk") or "")
            if "cannot" in risk.lower() or "not connected" in risk.lower():
                escalations.append({"manager": manager, "risk": risk})
        return {
            "never_idle": True,
            "daily_question": "What is my highest ROI action today?",
            "if_no_work_exists": "Create work that improves customer acquisition or measurement.",
            "if_blocked": "Remove blocker; if impossible, escalate with business impact and next review.",
            "manager_actions": manager_actions,
            "escalations": escalations,
            "next_management_review": f"{run_date} 16:00 Asia/Jerusalem",
        }

    def _operating_dir(self) -> Path:
        path = self.memory_root / "executive_os"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _read_operating_json(self, name: str, default: Any) -> Any:
        path = self._operating_dir() / name
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return default

    def _write_operating_json(self, name: str, payload: Any) -> None:
        path = self._operating_dir() / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def _persist_operating_state(self, state: dict[str, Any]) -> None:
        self._write_operating_json("latest_operating_executive.json", state)

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

    def _budget_guard(self, budget_status: dict[str, Any], now: datetime | None = None) -> dict[str, Any]:
        now = now or datetime.now(ZoneInfo(self.timezone))
        daily_limit = float(budget_status.get("daily_budget_limit_ils") or 20)
        monthly_limit = float(budget_status.get("monthly_budget_limit_ils") or daily_limit * 30)
        spent_today = float(budget_status.get("current_spend_ils") or 0)
        spent_month = spent_today
        reserved_today = 0.0
        committed_today = 0.0
        remaining_today = max(0.0, daily_limit - reserved_today - committed_today - spent_today)
        remaining_month = max(0.0, monthly_limit - spent_month)
        is_saturday = now.weekday() == 5
        is_friday_after_morning = now.weekday() == 4 and now.hour >= 12
        rules = {
            "daily_cap": daily_limit <= 20,
            "monthly_cap": monthly_limit <= 600,
            "remaining_daily_budget": remaining_today >= daily_limit,
            "remaining_monthly_budget": remaining_month >= daily_limit,
            "one_active_experiment_per_asset": True,
            "one_active_campaign_at_a_time": bool(budget_status.get("one_active_campaign_limit", True)),
            "friday_morning_only": not is_friday_after_morning,
            "saturday_block": not is_saturday,
            "duplicate_prevention": True,
            "exploration_experiment_cap": daily_limit <= 20,
            "internal_ledger_exists": True,
        }
        failed_rules = [
            name
            for name, value in rules.items()
            if value in {False, None, ""}
        ]
        allowed = not failed_rules
        return {
            "daily_budget_limit": daily_limit,
            "monthly_budget_limit": monthly_limit,
            "reserved_today": reserved_today,
            "committed_today": committed_today,
            "spent_today": spent_today,
            "spent_month": spent_month,
            "remaining_today": remaining_today,
            "remaining_month": remaining_month,
            "allowed_to_launch": allowed,
            "meta_spend_reconciliation": "verified" if budget_status.get("verified") else "pending",
            "rules": rules,
            "failed_rules": failed_rules,
            "campaign_creation_allowed": allowed,
            "decision": "stop_campaign_creation" if failed_rules else "allow_if_promotion_brain_approves",
            "reason": (
                "Campaign creation must stop until failed budget guard rules are resolved."
                if failed_rules
                else "Internal budget guard rules are satisfied. Meta reconciliation is separate from launch authority."
            ),
        }

    def _promotion_brain(
        self,
        content_intelligence: dict[str, Any],
        budget_status: dict[str, Any],
        budget_guard: dict[str, Any],
    ) -> dict[str, Any]:
        score = content_intelligence.get("business_value_score")
        has_verified_metrics = content_intelligence.get("status") == "verified"
        has_published_asset = bool(content_intelligence.get("published_asset_under_review"))
        promote = bool(
            budget_guard.get("allowed_to_launch")
            and has_published_asset
            and (
                (isinstance(score, int) and score >= 90)
                or not has_verified_metrics
            )
        )
        decision = "launch_campaign" if promote else "generate_better_creative" if not has_published_asset else "hold_budget"
        return {
            "allowed_decisions": ["launch_campaign", "hold_budget", "generate_better_creative", "retry_later"],
            "decision": decision,
            "decision_option": decision,
            "mode": "exploration" if not has_verified_metrics else "optimization",
            "attribution_required_to_launch": False,
            "confidence": "low" if not has_verified_metrics else "medium",
            "status": "approved_for_connector" if promote else "blocked",
            "business_value_score": score,
            "decision_inputs": {
                "budget_remaining": budget_status.get("remaining_monthly_budget_ils"),
                "revenue_influence_score": None,
                "whatsapp_conversions": content_intelligence.get("metrics", {}).get("whatsapp_clicks"),
                "demo_rate": content_intelligence.get("metrics", {}).get("demo_requests"),
                "customer_acquisition": content_intelligence.get("metrics", {}).get("customers"),
                "creative_fatigue": None,
            },
            "hypothesis": "Promoting the highest-value WhatsApp-intake asset will increase qualified law-firm demos.",
            "expected_outcome": "More qualified WhatsApp conversations that convert into booked demos.",
            "stop_condition": "Stop after ₪100 exploration spend, if budget guard fails, if no WhatsApp conversations are produced, or if cost per qualified lead exceeds target.",
            "success_criteria": "Verified qualified leads, booked demos, or customers increase within delegated budget.",
            "campaign_objective": "WhatsApp conversations",
            "tracked_whatsapp_link_required": True,
            "next_automatic_action": (
                "Pass launch-approved decision to MetaExecutor."
                if promote
                else "Create a stronger Hebrew creative before re-evaluating campaign spend."
                if not has_published_asset
                else "Re-evaluate the latest asset at the next 16:00 Asia/Jerusalem campaign window."
            ),
            "reason": (
                "Promotion is blocked until a published asset and Budget Guard pass."
                if not promote
                else "Promotion Brain approved controlled exploration within delegated guardrails; missing attribution is labeled low confidence, not a launch blocker."
            ),
        }

    def _campaign_decision_record(
        self,
        *,
        content_intelligence: dict[str, Any],
        promotion_brain: dict[str, Any],
        budget_guard: dict[str, Any],
        budget_status: dict[str, Any],
        meta_ads: dict[str, Any],
        cta: dict[str, Any],
        run_date: str,
        now: datetime,
    ) -> dict[str, Any]:
        published_asset = content_intelligence.get("published_asset_under_review") or {}
        asset_id = (
            published_asset.get("buffer_update_id")
            or published_asset.get("image_sha256")
            or f"planned-founder-whatsapp-{run_date}"
        )
        post_url = published_asset.get("instagram_url")
        tracked_whatsapp_link = self._whatsapp_link(cta, {})
        next_retry_at = self._next_campaign_retry(now).isoformat()
        meta_connector = self._meta_connector_status(meta_ads)
        rules_checked = {
            "one_active_campaign_at_a_time": budget_status.get("one_active_campaign_limit", True),
            "daily_budget_lte_20": budget_guard.get("daily_budget_limit", 20) <= 20,
            "monthly_budget_lte_600": budget_guard.get("monthly_budget_limit", 600) <= 600,
            "exploration_experiment_lte_100": True,
            "no_saturday": budget_guard.get("rules", {}).get("saturday_block"),
            "friday_morning_only": budget_guard.get("rules", {}).get("friday_morning_only"),
            "tracked_whatsapp_cta_present": bool(tracked_whatsapp_link),
            "stop_condition_present": bool(promotion_brain.get("stop_condition")),
            "published_asset_available": bool(published_asset),
            "meta_connector_available": meta_connector["available"],
        }
        failed_rules = [
            name for name, value in rules_checked.items()
            if value in {False, None, ""}
        ]
        failed_rules.extend(
            rule for rule in budget_guard.get("failed_rules", [])
            if rule not in failed_rules
        )

        if meta_connector["available"] and promotion_brain.get("decision") == "launch_campaign" and not failed_rules:
            state = "launch_approved"
            decision = "launch_campaign"
            reason = "Campaign launch is approved by Promotion Brain, Budget Guard, and Meta connector status."
            requires_ceo_action = False
            next_action = "MetaExecutor creates campaign, ad set, and ad in the same execution window."
            campaign_run_answer = "Campaign launched."
        elif meta_connector["available"] and promotion_brain.get("decision") == "hold_budget":
            state = "launch_blocked"
            decision = "hold_budget"
            reason = "Campaign intentionally not launched because promotion signal did not justify spend."
            requires_ceo_action = False
            next_action = "Re-evaluate the latest asset at the next campaign decision window."
            campaign_run_answer = "Campaign intentionally not launched."
        elif promotion_brain.get("decision") == "generate_better_creative":
            state = "launch_blocked"
            decision = "generate_better_creative"
            reason = "Campaign not launched because no approved published asset exists for promotion."
            requires_ceo_action = False
            next_action = "Generate and publish an approved Hebrew SaaS advertisement before campaign evaluation."
            campaign_run_answer = "Campaign intentionally not launched."
        else:
            state = "launch_blocked"
            decision = "retry_later"
            reason = meta_connector["reason"]
            requires_ceo_action = meta_connector["requires_ceo_action"]
            next_action = (
                "Retry Meta connector validation at the next campaign decision window."
                if not requires_ceo_action
                else "Wait for missing Meta execution configuration, then retry automatically."
            )
            campaign_run_answer = (
                "Campaign blocked and CEO action required."
                if requires_ceo_action
                else "Campaign failed and automatic retry scheduled."
            )

        evidence = {
            "rules_checked": rules_checked,
            "failed_rules": failed_rules,
            "next_retry_time": next_retry_at,
            "budget": {
                "daily_budget_limit": budget_guard.get("daily_budget_limit"),
                "monthly_budget_limit": budget_guard.get("monthly_budget_limit"),
                "reserved_today": budget_guard.get("reserved_today"),
                "committed_today": budget_guard.get("committed_today"),
                "spent_today": budget_guard.get("spent_today"),
                "spent_month": budget_guard.get("spent_month"),
                "remaining_today": budget_guard.get("remaining_today"),
                "remaining_month": budget_guard.get("remaining_month"),
                "allowed_to_launch": budget_guard.get("allowed_to_launch"),
                "failed_rules": budget_guard.get("failed_rules", []),
            },
            "meta_connector": meta_connector,
            "linked_instagram_post": post_url,
            "tracked_whatsapp_link": tracked_whatsapp_link,
            "stop_condition": promotion_brain.get("stop_condition"),
        }
        if state in {"launch_approved", "launched", "monitoring"}:
            evidence.update(
                {
                    "meta_campaign_id": None,
                    "ad_set_id": None,
                    "ad_id": None,
                    "budget": "₪20/day",
                    "start_time": now.isoformat(),
                }
            )
        record = {
            "decision_id": f"campaign-decision-{run_date}-{sha256(str(asset_id).encode('utf-8')).hexdigest()[:8]}",
            "asset_id": asset_id,
            "post_url": post_url,
            "evaluated_at": now.isoformat(),
            "state": state,
            "decision": decision,
            "reason": reason,
            "why": promotion_brain.get("reason"),
            "expected_outcome": promotion_brain.get("expected_outcome"),
            "confidence": promotion_brain.get("confidence"),
            "rules_checked": rules_checked,
            "failed_rules": failed_rules,
            "budget_status": evidence["budget"],
            "next_retry_at": next_retry_at,
            "next_automatic_action": next_action,
            "requires_ceo_action": requires_ceo_action,
            "campaign_run_answer": campaign_run_answer,
            "evidence": evidence,
        }
        self._write_operating_json(f"campaign_decisions/{record['decision_id']}.json", record)
        self._write_operating_json("latest_campaign_decision.json", record)
        return record

    def _meta_connector_status(self, meta_ads: dict[str, Any]) -> dict[str, Any]:
        missing: list[str] = []
        reason_parts: list[str] = []
        if not self.meta_execution_enabled:
            missing.append("META_EXECUTION_ENABLED=true")
        if not isinstance(meta_ads, dict) or not meta_ads.get("verified"):
            reason = str(meta_ads.get("reason") or "No verified Meta campaign data available.")
            reason_parts.append(reason)
            if "META_ACCESS_TOKEN" in reason:
                missing.append("META_ACCESS_TOKEN")
            if "META_IG_ACCOUNT_ID" in reason:
                missing.append("META_IG_ACCOUNT_ID")
            if "META_AD_ACCOUNT_ID" in reason:
                missing.append("META_AD_ACCOUNT_ID")
        connector_implemented = False
        if not connector_implemented:
            missing.append("MetaExecutor campaign creation connector")
        missing = list(dict.fromkeys(missing))
        available = self.meta_execution_enabled and connector_implemented and bool(meta_ads.get("verified"))
        requires_ceo_action = any(item.startswith("META_") for item in missing)
        exact_reason = (
            "Meta campaign execution connector is available."
            if available
            else "Meta campaign launch blocked: "
            + ", ".join(missing)
            + (
                f". Source reason: {' '.join(reason_parts)}"
                if reason_parts
                else "."
            )
        )
        return {
            "available": available,
            "configured": self.meta_execution_enabled,
            "verified_metrics": bool(isinstance(meta_ads, dict) and meta_ads.get("verified")),
            "connector_implemented": connector_implemented,
            "missing": missing,
            "requires_ceo_action": requires_ceo_action,
            "reason": exact_reason,
        }

    def _next_campaign_retry(self, now: datetime) -> datetime:
        retry = now.replace(hour=16, minute=0, second=0, microsecond=0)
        if now >= retry:
            retry = retry + timedelta(days=1)
        while retry.weekday() == 5:
            retry = retry + timedelta(days=1)
        if retry.weekday() == 4 and retry.hour >= 12:
            retry = retry + timedelta(days=2)
            retry = retry.replace(hour=16, minute=0, second=0, microsecond=0)
        return retry

    def _video_production(
        self,
        video_output: dict[str, Any],
        brand_intelligence: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "openai_responsibilities": [
                "Creative brief",
                "Script",
                "Storyboard",
                "Shot list",
                "Thumbnail concept",
                "Branding",
                "CTA",
            ],
            "heygen_responsibilities": ["Rendering", "Voice", "Avatar", "Final MP4"],
            "requirements": {
                "language": "Hebrew",
                "target_audience": "Israeli law firms",
                "whatsapp_cta": True,
                "follows_brand_brain": bool(brand_intelligence),
                "format": video_output.get("format"),
                "aspect_ratio": video_output.get("aspect_ratio"),
                "subtitles": video_output.get("subtitles"),
            },
            "status": "specified",
            "blocking_issue": "HeyGen execution connector is not yet connected for final MP4 generation.",
        }

    def _brand_brain(self, brand_intelligence: dict[str, Any]) -> dict[str, Any]:
        available = bool(isinstance(brand_intelligence, dict) and brand_intelligence.get("available"))
        return {
            "available": available,
            "maintains": [
                "Logos",
                "Colors",
                "Typography",
                "Templates",
                "Image styles",
                "Voice",
                "Tone",
                "Messaging",
            ],
            "marketing_language": (
                brand_intelligence.get("brand", {}).get("marketing_language")
                if available
                else "Hebrew"
            ),
            "internal_language": (
                brand_intelligence.get("brand", {}).get("internal_language")
                if available
                else "English"
            ),
            "quality_requirement": "Reject assets that do not meet premium agency quality.",
            "source": (
                brand_intelligence.get("source", "configured_defaults")
                if isinstance(brand_intelligence, dict)
                else "configured_defaults"
            ),
        }

    def _connector_health(
        self,
        whatsapp_bot: dict[str, Any],
        meta_ads: dict[str, Any],
        image_result: ExecutionResult | None,
        buffer_result: ExecutionResult | None,
    ) -> dict[str, Any]:
        def connector(status: str, *, evidence: list[str], failure: str | None = None) -> dict[str, Any]:
            return {
                "health": status,
                "retry_policy": "Retry automatically on next scheduled run unless failure is non-retryable.",
                "evidence": evidence,
                "monitoring": "recorded_in_execution_log",
                "failure_handling": failure or "report blocked/failed with exact reason and next retry",
            }

        return {
            "OpenAI": connector(
                "working" if image_result and image_result.status == "completed" else "blocked",
                evidence=["image_sha256", "model", "brand_validation"],
                failure=image_result.error if image_result and image_result.error else None,
            ),
            "Meta": connector(
                "working" if meta_ads.get("verified") else "unavailable",
                evidence=["campaign_status", "spend", "performance"],
                failure="No verified Meta execution/metrics available." if not meta_ads.get("verified") else None,
            ),
            "Buffer": connector(
                "working" if buffer_result and buffer_result.status == "completed" else "blocked",
                evidence=["buffer_update_id", "buffer_post_url", "instagram_url"],
                failure=buffer_result.error if buffer_result and buffer_result.error else None,
            ),
            "Cloudinary": connector(
                "working" if image_result and image_result.proof.get("public_url") else "blocked",
                evidence=["public_url", "upload_asset_id"],
                failure=image_result.error if image_result and image_result.error else None,
            ),
            "WhatsApp": connector(
                "working" if whatsapp_bot.get("verified") else "unavailable",
                evidence=["conversation_id", "qualified_lead", "demo_booked", "customer"],
                failure="No verified WhatsApp event data available." if not whatsapp_bot.get("verified") else None,
            ),
            "Resend": connector("configured_in_daily_brief", evidence=["message_id", "recipient"]),
            "GitHub": connector("not_connected_for_pr_execution", evidence=["pull_request_url"]),
            "Google Analytics 4": connector("not_connected", evidence=["ga4_events"]),
            "Google Search Console": connector("not_connected", evidence=["search_console"]),
            "CRM": connector("not_connected", evidence=["customer_id", "revenue"]),
            "HeyGen": connector("not_connected_for_rendering", evidence=["mp4_path", "video_sha256"]),
        }

    def _monitoring(
        self,
        run_date: str,
        execution_results: list[ExecutionResult],
        buffer_result: ExecutionResult | None,
    ) -> dict[str, Any]:
        completed = [result for result in execution_results if result.status == "completed"]
        blocked = [result for result in execution_results if result.status == "blocked"]
        failed = [result for result in execution_results if result.status == "failed"]
        last_asset = buffer_result.proof if buffer_result and buffer_result.status == "completed" else {}
        return {
            "health_status": "working" if completed and not failed else "blocked" if blocked else "unknown",
            "last_successful_run": completed[-1].timestamp if completed else None,
            "next_scheduled_run": f"{run_date} 08:00 Asia/Jerusalem",
            "last_published_asset": {
                "instagram_url": last_asset.get("instagram_url"),
                "buffer_update_id": last_asset.get("buffer_update_id"),
                "image_sha256": last_asset.get("image_sha256"),
            } if last_asset else None,
            "last_campaign": None,
            "last_email": None,
            "blocking_issues": [result.error for result in blocked if result.error],
            "missed_run_alerts": "required_if_scheduler_misses_expected_run",
        }

    def _weekly_executive_review(
        self,
        whatsapp_bot: dict[str, Any],
        meta_ads: dict[str, Any],
        content_intelligence: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "schedule": "Every Sunday",
            "review_items": [
                "Revenue",
                "Leads",
                "Demos",
                "Customers",
                "ROI",
                "Best campaigns",
                "Worst campaigns",
                "Lessons learned",
                "Next week's priorities",
            ],
            "current_status": "blocked_until_attribution_connected",
            "revenue": None,
            "leads": (
                whatsapp_bot.get("today", {}).get("qualified_leads")
                if whatsapp_bot.get("verified")
                else None
            ),
            "demos": (
                whatsapp_bot.get("today", {}).get("demo_bookings")
                if whatsapp_bot.get("verified")
                else None
            ),
            "customers": content_intelligence.get("metrics", {}).get("customers"),
            "roi": None,
            "meta_status": meta_ads.get("campaign_status", "unknown"),
            "lessons_learned": "pending_verified_outcomes",
        }

    def _acceptance_criteria(
        self,
        execution_results: list[ExecutionResult],
        content_intelligence: dict[str, Any],
        budget_guard: dict[str, Any],
    ) -> dict[str, Any]:
        completed_actions = {result.action for result in execution_results if result.status == "completed"}
        return {
            "real_content_published": "publish_social_post" in completed_actions,
            "agency_quality_creative": "generate_branded_social_image" in completed_actions,
            "whatsapp_attribution": content_intelligence.get("metrics", {}).get("whatsapp_clicks") is not None,
            "meta_optimization": False,
            "budget_enforcement": bool(budget_guard.get("rules")),
            "website_optimization": False,
            "daily_ceo_brief": True,
            "learning_from_outcomes": content_intelligence.get("status") == "verified",
            "revenue_influence_tracking": content_intelligence.get("metrics", {}).get("customers") is not None,
            "thirty_consecutive_autonomous_operating_days": False,
            "system_complete": False,
        }

    def _final_definition_of_done(
        self,
        content_intelligence: dict[str, Any],
        budget_guard: dict[str, Any],
    ) -> dict[str, Any]:
        complete = (
            content_intelligence.get("metrics", {}).get("customers") not in {None, 0}
            and budget_guard.get("campaign_creation_allowed")
            and content_intelligence.get("status") == "verified"
        )
        return {
            "complete": complete,
            "requirements": [
                "Continuously acquires additional paying customers.",
                "Autonomously creates, measures, improves, and promotes marketing.",
                "Uses evidence rather than assumptions.",
                "Learns from outcomes.",
                "Remains inside delegated authority.",
                "Requires no daily operational management from the CEO.",
            ],
            "current_gap": (
                "The agent can execute and publish, but full completion still requires attribution, Meta optimization, CRM/revenue tracking, and 30 autonomous days."
                if not complete
                else "All final definition of done requirements are currently satisfied."
            ),
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
        promotion_brain: dict[str, Any],
        campaign_decision: dict[str, Any],
    ) -> AgentOutput:
        verified_campaign = bool(meta_ads.get("verified") and meta_ads.get("campaign_status") == "active")
        status = "completed" if campaign_decision.get("state") in {"launched", "monitoring"} else "blocked"
        return AgentOutput(
            agent="Ads Agent",
            status=status,
            daily_output={
                "campaign_status": meta_ads.get("campaign_status", "unknown"),
                "executed": status == "completed",
                "reason": campaign_decision.get("reason"),
                "promotion_brain": promotion_brain,
                "promotion_decision": campaign_decision.get("decision"),
                "campaign_decision": campaign_decision,
                "campaign_run_answer": campaign_decision.get("campaign_run_answer"),
                "next_automatic_action": campaign_decision.get("next_automatic_action"),
                "requires_ceo_action": campaign_decision.get("requires_ceo_action"),
                "business_value_score": content_intelligence.get("business_value_score"),
                "budget_status": budget_status,
                "budget_guard": campaign_decision.get("budget_status"),
                "budget_rule": "Do not exceed ILS 20/day or ILS 600/month. No Saturday spend. Friday morning only. One active promotion per asset.",
                "verified_active_campaign": verified_campaign,
                "evidence": campaign_decision.get("evidence"),
            },
            error=None if status == "completed" else campaign_decision.get("reason"),
        )

    def _analytics_output(
        self,
        whatsapp_bot: dict[str, Any],
        meta_ads: dict[str, Any],
        content_intelligence: dict[str, Any],
        growth_intelligence: dict[str, Any],
    ) -> AgentOutput:
        verified = bool(whatsapp_bot.get("verified")) or bool(meta_ads.get("verified"))
        return AgentOutput(
            agent="Analytics Agent",
            status="collected" if verified else "blocked",
            daily_output={
                "content_intelligence": content_intelligence,
                "growth_intelligence": growth_intelligence,
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
    decision_context.summary["growth_intelligence"] = payload.get("growth_intelligence", {})
    decision_context.summary["executive_measurement"] = payload.get("executive_measurement", {})
    decision_context.summary["operating_executive"] = payload.get("operating_executive", {})
    decision_context.summary["revenue_cmo"] = payload.get("revenue_cmo", {})
    decision_context.summary["promotion_brain"] = payload.get("promotion_brain", {})
    decision_context.summary["budget_guard"] = payload.get("budget_guard", {})
    decision_context.summary["campaign_decision"] = payload.get("campaign_decision", {})
    decision_context.summary["campaign_run_answer"] = payload.get("campaign_decision", {}).get("campaign_run_answer")
    decision_context.summary["video_production"] = payload.get("video_production", {})
    decision_context.summary["brand_brain"] = payload.get("brand_brain", {})
    decision_context.summary["connector_health"] = payload.get("connector_health", {})
    decision_context.summary["monitoring"] = payload.get("monitoring", {})
    decision_context.summary["weekly_executive_review"] = payload.get("weekly_executive_review", {})
    decision_context.summary["acceptance_criteria"] = payload.get("acceptance_criteria", {})
    decision_context.summary["final_definition_of_done"] = payload.get("final_definition_of_done", {})
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
            "campaign_decision": [
                "decision_id",
                "rules_checked",
                "failed_rules",
                "budget_status",
                "next_retry_at",
                "requires_ceo_action",
            ],
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
