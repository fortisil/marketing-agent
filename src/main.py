from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
import json
import logging
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import FastAPI
import uvicorn

from src.briefs.generator import generate_brief
from src.channels.base import OutputResult
from src.channels.file_output import FileOutputChannel
from src.config import (
    Settings,
    load_ceo_constitution,
    load_company_config,
    load_company_knowledge,
    load_funnel_config,
    load_hebrew_style_guide,
    load_objectives_config,
    load_settings,
)
from src.decisions.engine import DecisionEngine
from src.execution.connectors import BufferExecutor
from src.execution.marketing_department import (
    MarketingDepartment,
    attach_marketing_department_output,
)
from src.logging_config import configure_logging
from src.memory.journal import write_evening_journal
from src.providers.brand import BrandProvider
from src.providers.marketing_platform import MarketingPlatformProvider
from src.providers.mock import MockMetricsProvider
from src.providers.website_repo import WebsiteRepoProvider
from src.providers.whatsapp_bot import WhatsAppBotProvider
from src.scheduler import start_scheduler


app = FastAPI(title="fortisil ai-executive-os", version="1.0.0")
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GeneratedBrief:
    company_config: dict[str, Any]
    decision_context: Any
    brief: str


@dataclass(frozen=True)
class MarketingExecution:
    company_config: dict[str, Any]
    decision_context: Any


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def _email_subject(company_config: dict[str, Any]) -> str:
    company_name = company_config["company"]["name"]
    today = datetime.now().strftime("%Y-%m-%d")
    return f"{company_name} CEO Brief - {today}"


def _email_payload(
    generated: GeneratedBrief,
    result: OutputResult,
    to_email: str | None = None,
) -> dict[str, str]:
    company_name = generated.company_config["company"]["name"]
    run_date = generated.decision_context.run_date
    return {
        "to": to_email or generated.company_config["company"]["recipient_email"],
        "subject": f"📊 {company_name} CEO Daily Brief – {run_date}",
        "body_markdown": generated.brief,
        "brief_path": str(result.paths["brief"]),
        "report_path": str(result.paths["report"]),
    }


def execute_marketing_workforce(settings: Settings) -> MarketingExecution:
    company_config = load_company_config(settings.company_config_path)
    objectives_config = load_objectives_config(settings.objectives_config_path)
    funnel_config = load_funnel_config(settings.funnel_config_path)
    ceo_constitution = load_ceo_constitution(settings.ceo_constitution_path)
    company_knowledge = load_company_knowledge(settings.knowledge_path)
    executive_knowledge = f"{ceo_constitution}\n\n---\n\n{company_knowledge}"
    logger.info("daily_generation_started")

    providers = [
        BrandProvider(company_config, settings.timezone, settings.brand_root, settings.assets_root),
        WebsiteRepoProvider(company_config, settings.timezone, settings.chatbot2u_repo_path),
        MarketingPlatformProvider(
            company_config=company_config,
            access_token=settings.meta_access_token,
            env_ad_account_id=settings.meta_ad_account_id,
            ig_account_id=settings.meta_ig_account_id,
            api_version=settings.meta_api_version,
            timezone=settings.timezone,
        ),
        WhatsAppBotProvider(
            provider=settings.whatsapp_provider,
            events_path=settings.whatsapp_events_path,
            webhook_url=settings.whatsapp_webhook_url,
            funnel_config=funnel_config,
            timezone=settings.timezone,
            app_env=settings.app_env,
            allow_mock_data=settings.allow_mock_data,
        ),
    ]
    if settings.app_env != "production" or settings.allow_mock_data:
        providers.insert(0, MockMetricsProvider(company_config, settings.timezone))
    snapshots = [provider.collect() for provider in providers]
    logger.info(
        "metrics_collected",
        extra={"_providers": [snapshot.provider for snapshot in snapshots]},
    )

    decision_context = DecisionEngine(
        company_config=company_config,
        objectives_config=objectives_config,
        company_knowledge=executive_knowledge,
        timezone=settings.timezone,
    ).evaluate(snapshots)
    marketing_department_output = MarketingDepartment(
        company_config=company_config,
        objectives_config=objectives_config,
        timezone=settings.timezone,
        social_publishing_enabled=settings.social_publishing_enabled,
        buffer_access_token=settings.buffer_access_token,
        buffer_profile_id=settings.buffer_profile_id,
        execution_dry_run=settings.execution_dry_run,
        image_generation_enabled=settings.image_generation_enabled,
        openai_api_key=settings.openai_api_key,
        openai_image_model=settings.openai_image_model,
        assets_root=settings.assets_root,
        asset_public_base_url=settings.asset_public_base_url,
        asset_upload_provider=settings.asset_upload_provider,
        cloudinary_cloud_name=settings.cloudinary_cloud_name,
        cloudinary_api_key=settings.cloudinary_api_key,
        cloudinary_api_secret=settings.cloudinary_api_secret,
        memory_root=settings.memory_path,
        meta_execution_enabled=settings.meta_execution_enabled,
    ).run(decision_context)
    attach_marketing_department_output(decision_context, marketing_department_output)
    logger.info(
        "decision_context_created",
        extra={"_run_date": decision_context.run_date},
    )
    return MarketingExecution(company_config=company_config, decision_context=decision_context)


def generate_daily_brief(settings: Settings) -> GeneratedBrief:
    hebrew_style_guide = load_hebrew_style_guide(settings.hebrew_style_guide_path)
    execution = execute_marketing_workforce(settings)

    brief = generate_brief(
        settings,
        execution.company_config,
        execution.decision_context,
        hebrew_style_guide,
    )
    return GeneratedBrief(
        company_config=execution.company_config,
        decision_context=execution.decision_context,
        brief=brief,
    )


def save_generated_brief(
    settings: Settings,
    generated: GeneratedBrief,
    sent: bool = False,
    dry_run: bool = False,
    delivery: dict[str, Any] | None = None,
) -> OutputResult:
    return FileOutputChannel(settings.memory_path, settings.timezone).deliver(
        decision_context=generated.decision_context,
        brief=generated.brief,
        sent=sent,
        dry_run=dry_run,
        delivery=delivery,
    )


def dry_run(settings: Settings) -> str:
    generated = generate_daily_brief(settings)
    print(generated.brief)
    logger.info("dry_run_completed")
    return generated.brief


def generate_brief_files(settings: Settings) -> OutputResult:
    generated = generate_daily_brief(settings)
    result = save_generated_brief(settings, generated, sent=False, dry_run=False)
    print(f"Brief saved: {result.paths['brief']}")
    print(f"Report saved: {result.paths['report']}")
    logger.info("brief_files_generated", extra={"_brief_path": str(result.paths["brief"])})
    return result


def execute_marketing(settings: Settings, *, require_business_artifact: bool = False) -> dict[str, Any]:
    execution = execute_marketing_workforce(settings)
    summary = execution.decision_context.summary
    results = summary.get("marketing_department", {}).get("execution_results", [])
    completed = [item for item in results if item.get("status") == "completed"]
    blocked = [item for item in results if item.get("status") == "blocked"]
    failed = [item for item in results if item.get("status") == "failed"]
    generated_assets = _generated_asset_artifacts(completed)
    published_artifacts = _published_business_artifacts(completed)
    output = FileOutputChannel(settings.memory_path, settings.timezone).deliver(
        decision_context=execution.decision_context,
        brief=_marketing_execution_markdown(summary),
        sent=False,
        dry_run=settings.execution_dry_run,
        delivery=None,
    )
    payload = {
        "status": (
            "completed"
            if published_artifacts
            else "failed"
            if failed
            else "blocked"
            if blocked
            else "asset_generated"
            if generated_assets
            else "no_execution"
        ),
        "business_artifact_created": bool(published_artifacts),
        "published_artifacts": published_artifacts,
        "generated_assets": generated_assets,
        "run_date": execution.decision_context.run_date,
        "completed": completed,
        "blocked": blocked,
        "failed": failed,
        "paths": {key: str(value) for key, value in output.paths.items()},
    }
    print(json.dumps(payload, ensure_ascii=False))
    if require_business_artifact and not published_artifacts:
        raise SystemExit(2)
    return payload


def check_connectors(settings: Settings) -> dict[str, Any]:
    buffer_check = BufferExecutor(
        access_token=settings.buffer_access_token,
        profile_id=settings.buffer_profile_id,
        timezone=settings.timezone,
        dry_run=settings.execution_dry_run,
    ).check_connection(create_validation_draft=True)
    payload = {
        "status": "ok" if buffer_check.get("status") == "ok" else "failed",
        "connectors": {
            "BufferExecutor": buffer_check,
        },
    }
    print(json.dumps(payload, ensure_ascii=False))
    if payload["status"] != "ok":
        raise SystemExit(2)
    return payload


def _published_business_artifacts(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    artifacts: list[dict[str, Any]] = []
    for result in results:
        proof = result.get("proof", {})
        if result.get("action") != "publish_social_post" or not isinstance(proof, dict):
            continue
        if proof.get("buffer_update_id") and proof.get("instagram_url") and proof.get("worker_id"):
            artifacts.append(
                {
                    "type": "instagram_post",
                    "buffer_update_id": proof["buffer_update_id"],
                    "instagram_url": proof["instagram_url"],
                    "timestamp": proof.get("timestamp") or result.get("timestamp"),
                    "caption_hash": proof.get("caption_hash"),
                    "image_sha256": proof.get("image_sha256"),
                    "worker_id": proof["worker_id"],
                }
            )
    return artifacts


def _generated_asset_artifacts(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    artifacts: list[dict[str, Any]] = []
    for result in results:
        proof = result.get("proof", {})
        if result.get("action") != "generate_branded_social_image" or not isinstance(proof, dict):
            continue
        if proof.get("public_url") and proof.get("sha256") and proof.get("worker_id"):
            artifacts.append(
                {
                    "type": "branded_image",
                    "public_url": proof["public_url"],
                    "sha256": proof["sha256"],
                    "timestamp": proof.get("timestamp") or result.get("timestamp"),
                    "worker_id": proof["worker_id"],
                }
            )
    return artifacts


def _marketing_execution_markdown(summary: dict[str, Any]) -> str:
    autonomy = summary.get("business_autonomy_index", {})
    completion = summary.get("autonomous_work_completion_rate", {})
    return "\n".join(
        [
            "# Autonomous Marketing Execution",
            "",
            f"Business Autonomy Index: {autonomy.get('overall_percent', 'unavailable')}%",
            f"Autonomous Work Completion Rate: {completion.get('success_rate_percent', 'unavailable')}%",
            "",
            "This file records the execution-only run. The structured report and execution log are the source of truth.",
        ]
    )


def send_now(settings: Settings) -> OutputResult:
    generated = generate_daily_brief(settings)
    recipient = settings.email_to or generated.company_config["company"]["recipient_email"]
    subject = f"📊 {generated.company_config['company']['name']} CEO Daily Brief – {generated.decision_context.run_date}"

    if not settings.resend_api_key or not settings.email_from:
        missing = "RESEND_API_KEY" if not settings.resend_api_key else "EMAIL_FROM"
        delivery = _delivery_status(
            channel="resend",
            status="skipped",
            recipient=recipient,
            timezone=settings.timezone,
            reason=f"{missing} is not configured.",
        )
        result = save_generated_brief(settings, generated, sent=False, dry_run=False, delivery=delivery)
        print(f"Brief saved: {result.paths['brief']}")
        print(f"Report saved: {result.paths['report']}")
        print("Resend email delivery is not configured.")
        print("Set RESEND_API_KEY and EMAIL_FROM in .env, then run python -m src.main --send-now again.")
        print("Until then, use the saved brief or ChatGPT/Gmail connector for manual delivery.")
        logger.info("send_now_saved_without_resend", extra={"_recipient": recipient})
        return result

    from src.channels.email_resend import send_email_resend

    delivery = send_email_resend(
        api_key=settings.resend_api_key,
        from_email=settings.email_from,
        to_email=recipient,
        subject=subject,
        body_markdown=generated.brief,
        timezone=settings.timezone,
    )
    result = save_generated_brief(
        settings,
        generated,
        sent=delivery["status"] == "sent",
        dry_run=False,
        delivery=delivery,
    )
    print(f"Brief saved: {result.paths['brief']}")
    print(f"Report saved: {result.paths['report']}")
    if delivery["status"] == "sent":
        print(f"Email sent via Resend to {recipient}.")
    else:
        print(f"Resend delivery failed for {recipient}. Check the report delivery status.")
    logger.info("send_now_completed", extra={"_delivery_status": delivery["status"]})
    return result


def generate_email_body(settings: Settings) -> dict[str, str]:
    generated = generate_daily_brief(settings)
    result = save_generated_brief(settings, generated, sent=False, dry_run=False)
    payload = _email_payload(generated, result, to_email=settings.email_to)
    print(json.dumps(payload, ensure_ascii=False))
    logger.info("email_body_generated", extra={"_brief_path": payload["brief_path"]})
    return payload


def _delivery_status(
    *,
    channel: str,
    status: str,
    recipient: str,
    timezone: str,
    reason: str = "",
) -> dict[str, Any]:
    payload = {
        "channel": channel,
        "status": status,
        "recipient": recipient,
        "timestamp": datetime.now(ZoneInfo(timezone)).isoformat(),
    }
    if reason:
        payload["reason"] = reason
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ChatBot2U AI CMO.")
    parser.add_argument("--send-now", action="store_true", help="Generate and send the brief immediately.")
    parser.add_argument("--dry-run", action="store_true", help="Generate the brief and print it without email.")
    parser.add_argument(
        "--generate-brief",
        action="store_true",
        help="Generate and save Markdown brief plus structured JSON report.",
    )
    parser.add_argument(
        "--generate-email-body",
        action="store_true",
        help="Generate/save the brief and print a clean JSON email payload.",
    )
    parser.add_argument(
        "--execute-marketing",
        action="store_true",
        help="Run autonomous marketing workforce, save logs, and print execution JSON without email.",
    )
    parser.add_argument(
        "--require-business-artifact",
        action="store_true",
        help="With --execute-marketing, exit non-zero unless a verified business artifact was created.",
    )
    parser.add_argument(
        "--check-connectors",
        action="store_true",
        help="Validate external execution connector credentials and access without sending a CEO brief.",
    )
    parser.add_argument(
        "--write-evening-journal",
        action="store_true",
        help="Write an evening Executive Journal from the latest daily report.",
    )
    parser.add_argument("--serve", action="store_true", help="Run the optional FastAPI health server.")
    parser.add_argument("--host", default="127.0.0.1", help="FastAPI host.")
    parser.add_argument("--port", default=8000, type=int, help="FastAPI port.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = load_settings()
    configure_logging("ERROR" if args.execute_marketing or args.check_connectors else settings.log_level)

    if args.dry_run:
        dry_run(settings)
        return

    if args.generate_brief:
        generate_brief_files(settings)
        return

    if args.generate_email_body:
        generate_email_body(settings)
        return

    if args.execute_marketing:
        execute_marketing(settings, require_business_artifact=args.require_business_artifact)
        return

    if args.check_connectors:
        check_connectors(settings)
        return

    if args.write_evening_journal:
        paths = write_evening_journal(settings.memory_path, settings.timezone)
        print(f"Executive journal saved: {paths['journal']}")
        print(f"Executive journal JSON saved: {paths['journal_json']}")
        return

    if args.send_now:
        send_now(settings)
        return

    if args.serve:
        uvicorn.run(app, host=args.host, port=args.port)
        return

    start_scheduler(settings, lambda: generate_brief_files(settings))


if __name__ == "__main__":
    main()
