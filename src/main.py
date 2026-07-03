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


def generate_daily_brief(settings: Settings) -> GeneratedBrief:
    company_config = load_company_config(settings.company_config_path)
    objectives_config = load_objectives_config(settings.objectives_config_path)
    funnel_config = load_funnel_config(settings.funnel_config_path)
    ceo_constitution = load_ceo_constitution(settings.ceo_constitution_path)
    company_knowledge = load_company_knowledge(settings.knowledge_path)
    executive_knowledge = f"{ceo_constitution}\n\n---\n\n{company_knowledge}"
    hebrew_style_guide = load_hebrew_style_guide(settings.hebrew_style_guide_path)
    logger.info("daily_generation_started")

    providers = [
        MockMetricsProvider(company_config, settings.timezone),
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
        ),
    ]
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
    logger.info(
        "decision_context_created",
        extra={"_run_date": decision_context.run_date},
    )

    brief = generate_brief(settings, company_config, decision_context, hebrew_style_guide)
    return GeneratedBrief(
        company_config=company_config,
        decision_context=decision_context,
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
    configure_logging(settings.log_level)

    if args.dry_run:
        dry_run(settings)
        return

    if args.generate_brief:
        generate_brief_files(settings)
        return

    if args.generate_email_body:
        generate_email_body(settings)
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
