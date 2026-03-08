"""Tavily Search API collector module."""

import logging
from datetime import datetime, timezone

import httpx

from app.agent.rss_collector import CollectedArticle
from app.core.config import settings

logger = logging.getLogger(__name__)

SEARCH_KEYWORDS = [
    "AI breakthrough 2025",
    "large language model news",
    "artificial intelligence latest",
    "tech industry news",
    "machine learning research",
    "open source AI",
]

# Simple in-memory monthly counter (resets on restart; good enough for dev)
_monthly_calls = {"month": 0, "count": 0}
MONTHLY_LIMIT = 900


def _check_quota() -> bool:
    current_month = datetime.now(timezone.utc).month
    if _monthly_calls["month"] != current_month:
        _monthly_calls["month"] = current_month
        _monthly_calls["count"] = 0
    return _monthly_calls["count"] < MONTHLY_LIMIT


def _record_call() -> None:
    current_month = datetime.now(timezone.utc).month
    if _monthly_calls["month"] != current_month:
        _monthly_calls["month"] = current_month
        _monthly_calls["count"] = 0
    _monthly_calls["count"] += 1


async def search_tavily(keywords: list[str] | None = None) -> list[CollectedArticle]:
    """Search for tech/AI news using Tavily API."""
    if not settings.TAVILY_API_KEY:
        logger.warning("Tavily API key not configured, skipping search")
        return []

    if not _check_quota():
        logger.warning(f"Tavily monthly quota nearly exhausted ({_monthly_calls['count']}), skipping")
        return []

    search_terms = keywords or SEARCH_KEYWORDS
    articles: list[CollectedArticle] = []

    async with httpx.AsyncClient(timeout=30) as client:
        for term in search_terms:
            if not _check_quota():
                break

            try:
                resp = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": settings.TAVILY_API_KEY,
                        "query": term,
                        "search_depth": "basic",
                        "max_results": 5,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                _record_call()

                for result in data.get("results", []):
                    articles.append(
                        CollectedArticle(
                            title=result.get("title", "").strip(),
                            url=result.get("url", "").strip(),
                            source_name="Tavily Search",
                            summary=result.get("content", "")[:500] if result.get("content") else None,
                        )
                    )
                logger.info(f"Tavily: found {len(data.get('results', []))} results for '{term}'")
            except Exception as e:
                logger.warning(f"Tavily: search failed for '{term}': {e}")
                continue

    return articles
