"""RSS 订阅源收集模块。"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlparse

import feedparser
import httpx

logger = logging.getLogger(__name__)

# 允许的 RSS 源协议
ALLOWED_SCHEMES = {"http", "https"}

# 禁止访问的私有 IP 范围（防止 SSRF）
BLOCKED_HOSTS = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
    "169.254.169.254",  # AWS metadata
}


@dataclass
class CollectedArticle:
    title: str
    url: str
    source_name: str
    published_at: datetime | None = None
    summary: str | None = None


def _validate_feed_url(url: str) -> bool:
    """验证 RSS 源 URL 是否安全，防止 SSRF 攻击。"""
    try:
        parsed = urlparse(url)
        # 只允许 http/https
        if parsed.scheme.lower() not in ALLOWED_SCHEMES:
            logger.warning(f"Blocked URL with disallowed scheme: {url}")
            return False
        # 阻止私有 IP 访问
        hostname = parsed.hostname or ""
        if hostname.lower() in BLOCKED_HOSTS:
            logger.warning(f"Blocked URL with private hostname: {url}")
            return False
        # 阻止内网 IP 格式 (简单检查)
        if hostname.startswith("192.168.") or hostname.startswith("10.") or hostname.startswith("172."):
            if hostname.startswith("172.") and len(hostname.split(".")) >= 2:
                second_octet = int(hostname.split(".")[1])
                if 16 <= second_octet <= 31:
                    logger.warning(f"Blocked URL with private IP: {url}")
                    return False
        return True
    except Exception as e:
        logger.warning(f"Failed to validate URL {url}: {e}")
        return False


async def fetch_rss_feeds(sources: list[dict]) -> list[CollectedArticle]:
    """从 RSS 源列表获取文章。

    每个源字典应包含：name, feed_url, category
    """
    articles: list[CollectedArticle] = []

    async with httpx.AsyncClient(timeout=30) as client:
        for source in sources:
            feed_url = source.get("feed_url", "")
            # 验证 URL 防止 SSRF
            if not _validate_feed_url(feed_url):
                logger.warning(f"Skipping invalid or blocked RSS URL: {feed_url}")
                continue

            try:
                resp = await client.get(feed_url)
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
