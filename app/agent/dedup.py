"""内容去重模块。"""

import logging
from difflib import SequenceMatcher

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.rss_collector import CollectedArticle
from app.models.news import NewsArticle

logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 0.85


def _title_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


async def deduplicate(
    articles: list[CollectedArticle],
    db: AsyncSession,
) -> list[CollectedArticle]:
    """移除数据库中已存在的文章。

    使用 URL 精确匹配 + 标题模糊匹配（>85% 相似度）。
    """
    if not articles:
        return []

    # 从数据库获取已有的 URL 和标题
    result = await db.execute(
        select(NewsArticle.original_url, NewsArticle.original_title)
    )
    existing = result.all()
    existing_urls = {row[0] for row in existing}
    existing_titles = [row[1] for row in existing]

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
