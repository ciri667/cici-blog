"""Content deduplication module."""

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
    """Remove articles that already exist in the database.

    Uses URL exact match + title fuzzy match (>85% similarity).
    """
    if not articles:
        return []

    # Get existing URLs and titles from DB
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

        # URL exact match
        if article.url in existing_urls:
            continue

        # Title fuzzy match
        is_duplicate = False
        for existing_title in existing_titles:
            if _title_similarity(article.title, existing_title) > SIMILARITY_THRESHOLD:
                is_duplicate = True
                break

        if not is_duplicate:
            unique.append(article)
            # Also check against articles in current batch
            existing_titles.append(article.title)
            existing_urls.add(article.url)

    logger.info(f"Dedup: {len(articles)} → {len(unique)} unique articles")
    return unique
