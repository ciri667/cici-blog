"""Tavily 搜索 API 收集模块。"""

import asyncio
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

# 简化的内存月度计数器（重启时重置；开发环境足够用）
# 添加异步锁防止并发问题
_monthly_calls = {"month": 0, "count": 0}
_quota_lock = asyncio.Lock()
MONTHLY_LIMIT = 900


async def _check_and_record_quota() -> bool:
    """原子性地检查并增加配额计数。"""
    global _monthly_calls

    async with _quota_lock:
        current_month = datetime.now(timezone.utc).month
        if _monthly_calls["month"] != current_month:
            _monthly_calls["month"] = current_month
            _monthly_calls["count"] = 0

        if _monthly_calls["count"] >= MONTHLY_LIMIT:
            return False

        _monthly_calls["count"] += 1
        return True


async def search_tavily(keywords: list[str] | None = None) -> list[CollectedArticle]:
    """使用 Tavily API 搜索科技/AI 新闻。"""
    if not settings.TAVILY_API_KEY:
        logger.warning("Tavily API key not configured, skipping search")
        return []

    if not await _check_and_record_quota():
        logger.warning(f"Tavily monthly quota nearly exhausted ({_monthly_calls['count']}), skipping")
        return []

    search_terms = keywords or SEARCH_KEYWORDS
    articles: list[CollectedArticle] = []

    async with httpx.AsyncClient(timeout=30) as client:
        for term in search_terms:
            # 每次调用前检查配额
            if not await _check_and_record_quota():
                break

            try:
                resp = await client.post(
                    "https://api.tavily.com/search",
                    # 注意：Tavily API 要求 api_key 在 body 中，这是设计限制
                    # 日志已配置为不记录敏感信息
                    json={
                        "api_key": settings.TAVILY_API_KEY,
                        "query": term,
                        "search_depth": "basic",
                        "max_results": 5,
                    },
                )
                resp.raise_for_status()
                data = resp.json()

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
                # 不要记录完整的请求信息，因为包含 API key
                logger.warning(f"Tavily: search failed for '{term}': {type(e).__name__}")
                continue

    return articles
