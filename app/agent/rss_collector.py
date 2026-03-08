"""RSS 订阅源收集模块。"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

import feedparser
import httpx

logger = logging.getLogger(__name__)


@dataclass
class CollectedArticle:
    title: str
    url: str
    source_name: str
    published_at: datetime | None = None
    summary: str | None = None


async def fetch_rss_feeds(sources: list[dict]) -> list[CollectedArticle]:
    """从 RSS 源列表获取文章。

    每个源字典应包含：name, feed_url, category
    """
    articles: list[CollectedArticle] = []

    async with httpx.AsyncClient(timeout=30) as client:
        for source in sources:
            try:
                resp = await client.get(source["feed_url"])
                resp.raise_for_status()
                feed = feedparser.parse(resp.text)

                for entry in feed.entries[:20]:  # 每个源限制数量
                    pub_date = None
                    if hasattr(entry, "published_parsed") and entry.published_parsed:
                        pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)

                    articles.append(
                        CollectedArticle(
                            title=entry.get("title", "").strip(),
                            url=entry.get("link", "").strip(),
                            source_name=source["name"],
                            published_at=pub_date,
                            summary=entry.get("summary", "")[:500] if entry.get("summary") else None,
                        )
                    )
                logger.info(f"RSS: fetched {len(feed.entries)} entries from {source['name']}")
            except Exception as e:
                logger.warning(f"RSS: failed to fetch {source['name']}: {e}")
                continue

    return articles
