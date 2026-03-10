"""RSS 订阅源收集模块。"""

import html
import ipaddress
import logging
import re
import socket
import unicodedata
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

# RSS 响应体大小限制（字节）
MAX_RSS_RESPONSE_SIZE = 500_000


def _is_private_ip(hostname: str) -> bool:
    """解析 hostname 并检查解析后的地址是否为私有/保留地址。"""
    # 首先尝试直接作为 IP 地址解析（处理十进制、八进制、IPv6 等编码）
    try:
        addr = ipaddress.ip_address(hostname)
        return (
            addr.is_private
            or addr.is_loopback
            or addr.is_link_local
            or addr.is_reserved
        )
    except ValueError:
        pass

    # 作为域名解析，检查所有解析出的 IP
    try:
        infos = socket.getaddrinfo(hostname, None)
        for info in infos:
            ip_str = info[4][0]
            addr = ipaddress.ip_address(ip_str)
            if (
                addr.is_private
                or addr.is_loopback
                or addr.is_link_local
                or addr.is_reserved
            ):
                return True
    except (socket.gaierror, ValueError):
        # 解析失败时采用保守策略：阻止
        return True

    return False


def _sanitize_text(text: str, max_len: int = 500) -> str:
    """清理 RSS 内容中的 HTML 标签和实体，防止 XSS。"""
    if not text:
        return ""
    # 移除 HTML 标签
    text = re.sub(r"<[^>]+>", "", text)
    # 解码 HTML 实体
    text = html.unescape(text)
    # 移除控制字符（保留换行、制表）
    text = "".join(
        ch for ch in text if unicodedata.category(ch)[0] != "C" or ch in "\n\r\t"
    )
    return text.strip()[:max_len]


def _sanitize_url(url: str) -> str:
    """验证并清理 URL，只允许 http/https 协议。"""
    if not url:
        return ""
    try:
        parsed = urlparse(url)
        if parsed.scheme.lower() not in ALLOWED_SCHEMES:
            return ""
        return url.strip()
    except Exception:
        return ""


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
        # 提取 hostname
        hostname = parsed.hostname or ""
        if not hostname:
            logger.warning(f"Blocked URL with no hostname: {url}")
            return False
        # 阻止已知私有 hostname
        if hostname.lower() in BLOCKED_HOSTS:
            logger.warning(f"Blocked URL with private hostname: {url}")
            return False
        # 使用 ipaddress 模块检查私有/保留 IP（支持所有编码格式）
        if _is_private_ip(hostname):
            logger.warning(f"Blocked URL with private/reserved IP: {url}")
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
                # 限制响应体大小，防止内存耗尽和解析超时
                content = resp.text[:MAX_RSS_RESPONSE_SIZE]
                feed = feedparser.parse(content)

                for entry in feed.entries[:20]:  # 每个源限制数量
                    pub_date = None
                    if hasattr(entry, "published_parsed") and entry.published_parsed:
                        pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)

                    # 清理标题和摘要中的 HTML，防止 XSS
                    title = _sanitize_text(entry.get("title", ""), max_len=500)
                    summary = _sanitize_text(entry.get("summary", ""), max_len=500) if entry.get("summary") else None
                    # 验证 URL 协议
                    url = _sanitize_url(entry.get("link", ""))

                    if not title or not url:
                        continue

                    articles.append(
                        CollectedArticle(
                            title=title,
                            url=url,
                            source_name=source["name"],
                            published_at=pub_date,
                            summary=summary,
                        )
                    )
                logger.info(f"RSS: fetched {len(feed.entries)} entries from {source['name']}")
            except Exception as e:
                logger.warning(f"RSS: failed to fetch {source['name']}: {e}")
                continue

    return articles
