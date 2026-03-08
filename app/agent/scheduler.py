"""APScheduler 定时任务调度配置。"""

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def _run_pipeline_sync():
    """从同步调度回调运行异步流水线的包装函数。"""
    from app.agent.pipeline import run_pipeline

    loop = asyncio.get_event_loop()
    loop.create_task(run_pipeline())


def start_scheduler():
    """启动 APScheduler，每 4 小时运行一次 Agent 流水线。"""
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
    """停止调度器。"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Agent scheduler stopped")
