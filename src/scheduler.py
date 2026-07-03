from __future__ import annotations

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from src.config import Settings


def start_scheduler(settings: Settings, job) -> None:
    scheduler = BlockingScheduler(timezone=settings.timezone)
    trigger = CronTrigger(
        hour=settings.brief_hour,
        minute=settings.brief_minute,
        timezone=settings.timezone,
    )
    scheduler.add_job(job, trigger, id="chatbot2u_daily_ceo_brief", replace_existing=True)
    scheduler.start()
