"""Agent 相关初始化任务的引导辅助函数。"""

import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select

from app.agent.rss_defaults import DEFAULT_RSS_SOURCES
from app.core.database import async_session_factory
from app.models.news import RssSource

logger = logging.getLogger(__name__)


async def seed_default_rss_sources() -> None:
    """当默认 RSS 源不存在时插入。"""
    try:
        async with async_session_factory() as db:
            result = await db.execute(select(RssSource.feed_url))
            existing_urls = set(result.scalars().all())

            created = False
            for source in DEFAULT_RSS_SOURCES:
                if source["feed_url"] in existing_urls:
                    continue
                db.add(RssSource(**source))
                created = True

            if created:
                await db.commit()
    except SQLAlchemyError:
        logger.exception("初始化默认 RSS 源失败。")
