"""新闻文章公共 API 及管理端点。"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_admin
from app.models.news import NewsArticle
from app.models.user import User
from app.schemas.news import (
    NewsAdminUpdate,
    NewsArticleResponse,
    NewsListItem,
    NewsListResponse,
)

router = APIRouter(tags=["news"])


# --- 公共端点 ---


@router.get("/news", response_model=NewsListResponse)
async def list_news(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(NewsArticle).where(NewsArticle.status == "published")

    if category:
        query = query.where(NewsArticle.category == category)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(
        NewsArticle.published_at.desc().nullslast(),
        NewsArticle.created_at.desc(),
    )
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    articles = result.scalars().all()

    return NewsListResponse(
        items=[NewsListItem.model_validate(a) for a in articles],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/news/{slug}", response_model=NewsArticleResponse)
async def get_news_article(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(NewsArticle).where(NewsArticle.slug == slug)
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    return NewsArticleResponse.model_validate(article)


# --- 管理端点 ---


@router.get("/admin/news", response_model=NewsListResponse)
async def admin_list_news(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    query = select(NewsArticle)
    if status:
        query = query.where(NewsArticle.status == status)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(
        NewsArticle.published_at.desc().nullslast(),
        NewsArticle.created_at.desc(),
    )
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    articles = result.scalars().all()

    return NewsListResponse(
        items=[NewsListItem.model_validate(a) for a in articles],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.put("/admin/news/{article_id}", response_model=NewsArticleResponse)
async def admin_update_news_status(
    article_id: int,
    data: NewsAdminUpdate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(NewsArticle).where(NewsArticle.id == article_id)
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    updates = data.model_dump(exclude_unset=True)
    status = updates.pop("status", None)

    for key, value in updates.items():
        if key == "tags" and value is not None:
            value = [tag.strip() for tag in value if tag and tag.strip()]
            value = value or None
        setattr(article, key, value)

    if status is not None:
        article.status = status

    if article.status == "published" and article.published_at is None:
        from datetime import datetime, timezone

        article.published_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(article)
    return NewsArticleResponse.model_validate(article)


@router.delete("/admin/news/{article_id}", status_code=204)
async def admin_delete_news(
    article_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(NewsArticle).where(NewsArticle.id == article_id)
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    await db.delete(article)
    await db.commit()
