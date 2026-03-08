"""LLM processing module for summary, commentary, and tagging."""

import json
import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

CATEGORIES = [
    "大模型", "芯片", "机器人", "开源", "自动驾驶",
    "云计算", "网络安全", "区块链", "量子计算", "生物科技",
    "创业投资", "产品发布", "行业分析", "政策法规", "其他",
]


async def generate_summary(title: str, content: str) -> str:
    """Generate a 100-200 word Chinese summary using GPT-4o-mini."""
    if not settings.OPENAI_API_KEY:
        logger.warning("OpenAI API key not configured, using original content as summary")
        return content[:200] if content else title

    prompt = f"""请为以下科技新闻生成一段100-200字的中文摘要，概括核心内容。

标题：{title}
内容：{content[:3000]}

要求：
- 使用中文
- 100-200字
- 客观概括核心信息
- 不要添加个人观点"""

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 500,
                    "temperature": 0.3,
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.error(f"Summary generation failed: {e}")
        return content[:200] if content else title


async def generate_commentary(title: str, content: str, summary: str) -> str:
    """Generate a 500-1500 word Chinese commentary article using Claude API."""
    if not settings.ANTHROPIC_API_KEY:
        logger.warning("Anthropic API key not configured, skipping commentary")
        return ""

    prompt = f"""你是一位资深科技评论员，请基于以下新闻撰写一篇500-1500字的中文评论文章。

新闻标题：{title}
新闻摘要：{summary}
原文内容：{content[:4000]}

要求：
1. 用中文撰写
2. 500-1500字
3. 包含以下部分：
   - 事件分析：这则新闻的核心内容和背景
   - 技术观点：从技术角度分析其意义和创新点
   - 行业影响：对行业发展可能产生的影响
   - 个人看法：给出你的独立判断和预测
4. 语言风格：专业但易读，有深度但不晦涩
5. 不要使用 Markdown 标题语法（不要用 # 号）"""

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 4000,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["content"][0]["text"].strip()
    except Exception as e:
        logger.error(f"Commentary generation failed: {e}")
        return ""


async def classify_article(title: str, summary: str) -> tuple[str, list[str]]:
    """Classify article into category and tags using GPT-4o-mini."""
    if not settings.OPENAI_API_KEY:
        return "其他", []

    categories_str = ", ".join(CATEGORIES)
    prompt = f"""请对以下科技新闻进行分类和打标。

标题：{title}
摘要：{summary}

可选分类（选一个最匹配的）：{categories_str}

请以JSON格式返回，例如：
{{"category": "大模型", "tags": ["GPT", "自然语言处理", "OpenAI"]}}

要求：
- category 必须从上面的可选分类中选
- tags 提供2-5个相关标签，使用中文
- 只返回JSON，不要其他文字"""

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 200,
                    "temperature": 0.1,
                },
            )
            resp.raise_for_status()
            text = resp.json()["choices"][0]["message"]["content"].strip()
            # Parse JSON from response
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0]
            data = json.loads(text)
            category = data.get("category", "其他")
            tags = data.get("tags", [])
            if category not in CATEGORIES:
                category = "其他"
            return category, tags[:5]
    except Exception as e:
        logger.error(f"Classification failed: {e}")
        return "其他", []
