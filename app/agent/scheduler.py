"""APScheduler 定时任务调度配置。"""

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def _run_pipeline_sync() -> None:
    """从同步调度回调运行异步流水线的包装函数。"""
    from app.agent.pipeline import run_pipeline

    try:
        # 尝试获取正在运行的事件循环
        loop = asyncio.get_running_loop()
        loop.create_task(run_pipeline())
    except RuntimeError:
        # 如果没有运行中的事件循环，创建一个新的
        logger.warning("No running event loop, creating new one for pipeline")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(run_pipeline())
        finally:
            loop.close()


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
