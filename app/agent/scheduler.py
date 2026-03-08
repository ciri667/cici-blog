"""APScheduler configuration for periodic agent runs."""

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def _run_pipeline_sync():
    """Wrapper to run async pipeline from sync scheduler callback."""
    from app.agent.pipeline import run_pipeline

    loop = asyncio.get_event_loop()
    loop.create_task(run_pipeline())


def start_scheduler():
    """Start the APScheduler with agent pipeline job every 4 hours."""
    scheduler.add_job(
        _run_pipeline_sync,
        "interval",
        hours=4,
        id="agent_pipeline",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Agent scheduler started (every 4 hours)")


def stop_scheduler():
    """Stop the scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Agent scheduler stopped")
