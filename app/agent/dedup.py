"""内容去重模块。"""

import logging
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.rss_collector import CollectedArticle
from app.models.news import NewsArticle

logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 0.85

# 标题模糊匹配的时间窗口（天），减少内存和计算开销
TITLE_LOOKBACK_DAYS = 30


def _title_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


async def deduplicate(
    articles: list[CollectedArticle],
    db: AsyncSession,
) -> list[CollectedArticle]:
    """移除数据库中已存在的文章。

    使用 URL 精确匹配 + 标题模糊匹配（>85% 相似度）。
    只查询最近 30 天的文章标题进行模糊匹配。
    """
    if not articles:
        return []

    # 计算时间窗口
    cutoff = datetime.now(timezone.utc) - timedelta(days=TITLE_LOOKBACK_DAYS)

    # 从数据库获取已有的 URL（全量，用于精确匹配）
    result = await db.execute(select(NewsArticle.original_url))
    existing_urls = {row[0] for row in result.all()}

    # 只获取最近 30 天的标题用于模糊匹配
    result = await db.execute(
        select(NewsArticle.original_title).where(
            NewsArticle.created_at >= cutoff
        )
    )
    existing_titles = [row[0] for row in result.all()]

    unique: list[CollectedArticle] = []
    for article in articles:
        if not article.url or not article.title:
            continue

        # URL 精确匹配
        if article.url in existing_urls:
            continue

        # 标题模糊匹配
        is_duplicate = False
        for existing_title in existing_titles:
            if _title_similarity(article.title, existing_title) > SIMILARITY_THRESHOLD:
                is_duplicate = True
                break

        if not is_duplicate:
            unique.append(article)
            # 同时检查当前批次中的文章
            existing_titles.append(article.title)
            existing_urls.add(article.url)

    logger.info(f"Dedup: {len(articles)} → {len(unique)} unique articles")
    return unique
