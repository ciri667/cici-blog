"""Agent Pipeline: collect → deduplicate → AI process → store."""

import logging
import re
import unicodedata
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.dedup import deduplicate
from app.agent.llm_processor import classify_article, generate_commentary, generate_summary
from app.agent.rss_collector import CollectedArticle, fetch_rss_feeds
from app.agent.search_collector import search_tavily
from app.core.database import async_session_factory
from app.models.news import AgentRun, NewsArticle, RssSource

logger = logging.getLogger(__name__)

_running = False


def _slugify(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[\s_/\\]+", "-", text)
    text = re.sub(r"[^\w\-]", "", text, flags=re.UNICODE)
    text = re.sub(r"-{2,}", "-", text)
    text = text.strip("-").lower()
    if len(text) > 200:
        text = text[:200].rsplit("-", 1)[0]
    return text or "untitled"


async def _unique_slug(db: AsyncSession, base_slug: str) -> str:
    slug = base_slug
    suffix = 0
    while True:
        result = await db.execute(
            select(NewsArticle.id).where(NewsArticle.slug == slug)
        )
        if result.scalar_one_or_none() is None:
            return slug
        suffix += 1
        slug = f"{base_slug}-{suffix}"


async def run_pipeline() -> None:
    """Execute the full agent pipeline."""
    global _running

    if _running:
        logger.info("Pipeline already running, skipping")
        return

    _running = True
    logger.info("Agent pipeline started")

    async with async_session_factory() as db:
        # Create run record
        run = AgentRun(status="running")
        db.add(run)
        await db.commit()
        await db.refresh(run)

        try:
            # Stage 1: Collect from RSS
            rss_result = await db.execute(
                select(RssSource).where(RssSource.is_active == True)
            )
            rss_sources = rss_result.scalars().all()
            source_dicts = [
                {"name": s.name, "feed_url": s.feed_url, "category": s.category}
                for s in rss_sources
            ]

            rss_articles = await fetch_rss_feeds(source_dicts)

            # Stage 1b: Collect from Tavily
            search_articles = await search_tavily()

            all_articles = rss_articles + search_articles
            run.articles_found = len(all_articles)
            logger.info(f"Collected {len(all_articles)} total articles")

            # Stage 2: Deduplicate
            unique_articles = await deduplicate(all_articles, db)

            # Stage 3 & 4: AI process and store
            created_count = 0
            for article in unique_articles:
                try:
                    article_content = article.summary or article.title

                    # Generate summary
                    summary = await generate_summary(article.title, article_content)

                    # Generate commentary
                    commentary = await generate_commentary(
                        article.title, article_content, summary
                    )

                    # Classify
                    category, tags = await classify_article(article.title, summary)

                    # Generate slug
                    slug = await _unique_slug(db, _slugify(article.title))

                    # Store
                    news = NewsArticle(
                        title=article.title,
                        slug=slug,
                        original_url=article.url,
                        original_title=article.title,
                        source_name=article.source_name,
                        summary=summary,
                        ai_commentary=commentary,
                        tags=tags,
                        category=category,
                        status="pending",
                        fetched_at=datetime.now(timezone.utc),
                    )
                    db.add(news)
                    await db.flush()
                    created_count += 1
                    logger.info(f"Created news article: {article.title[:50]}...")
                except Exception as e:
                    logger.error(f"Failed to process article '{article.title[:50]}': {e}")
                    continue

            # Update run record
            run.articles_created = created_count
            run.status = "success"
            run.finished_at = datetime.now(timezone.utc)
            await db.commit()

            logger.info(
                f"Pipeline complete: {run.articles_found} found, "
                f"{len(unique_articles)} unique, {created_count} created"
            )

            # Update last_fetched_at for RSS sources
            for source in rss_sources:
                source.last_fetched_at = datetime.now(timezone.utc)
            await db.commit()

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            run.status = "failed"
            run.error_log = str(e)
            run.finished_at = datetime.now(timezone.utc)
            await db.commit()
            raise
        finally:
            _running = False
