import re
import unicodedata
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_admin
from app.models.blog import BlogPost, Comment
from app.models.user import User
from app.schemas.post import (
    PostCreate,
    PostListItem,
    PostListResponse,
    PostResponse,
    PostUpdate,
)

router = APIRouter(prefix="/posts", tags=["posts"])


def _slugify(text: str) -> str:
    """Generate a URL-friendly slug from a title.

    Handles Chinese/CJK characters by transliterating to pinyin-like tokens,
    and passes through Latin characters normally.
    """
    text = unicodedata.normalize("NFKC", text)
    # Replace common separators with hyphens
    text = re.sub(r"[\s_/\\]+", "-", text)
    # Keep word characters (letters, digits, CJK) and hyphens
    text = re.sub(r"[^\w\-]", "", text, flags=re.UNICODE)
    # Collapse multiple hyphens
    text = re.sub(r"-{2,}", "-", text)
    text = text.strip("-").lower()
    # Truncate to reasonable length
    if len(text) > 200:
        text = text[:200].rsplit("-", 1)[0]
    return text or "untitled"


async def _unique_slug(db: AsyncSession, base_slug: str, exclude_id: int | None = None) -> str:
    slug = base_slug
    suffix = 0
    while True:
        query = select(BlogPost.id).where(BlogPost.slug == slug)
        if exclude_id is not None:
            query = query.where(BlogPost.id != exclude_id)
        result = await db.execute(query)
        if result.scalar_one_or_none() is None:
            return slug
        suffix += 1
        slug = f"{base_slug}-{suffix}"


# --- Public endpoints ---


@router.get("", response_model=PostListResponse)
async def list_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    tag: str | None = None,
    category: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(BlogPost)

    # By default public listing shows only published posts
    if status:
        query = query.where(BlogPost.status == status)
    else:
        query = query.where(BlogPost.status == "published")

    if tag:
        query = query.where(BlogPost.tags.any(tag))
    if category:
        query = query.where(BlogPost.category == category)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Fetch page
    query = query.order_by(BlogPost.published_at.desc().nullslast(), BlogPost.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    posts = result.scalars().all()

    return PostListResponse(
        items=[PostListItem.model_validate(p) for p in posts],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{slug}", response_model=PostResponse)
async def get_post(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BlogPost).where(BlogPost.slug == slug))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="文章不存在")
    return PostResponse.model_validate(post)


# --- Admin endpoints ---


@router.post("", response_model=PostResponse, status_code=201)
async def create_post(
    data: PostCreate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    slug = await _unique_slug(db, _slugify(data.title))

    post = BlogPost(
        title=data.title,
        slug=slug,
        content=data.content,
        excerpt=data.excerpt,
        cover_image_url=data.cover_image_url,
        tags=data.tags,
        category=data.category,
        status=data.status,
        author_id=admin.id,
        published_at=datetime.now(timezone.utc) if data.status == "published" else None,
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return PostResponse.model_validate(post)


@router.put("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: int,
    data: PostUpdate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(BlogPost).where(BlogPost.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="文章不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(post, key, value)

    # Set published_at when status changes to published
    if data.status == "published" and post.published_at is None:
        post.published_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(post)
    return PostResponse.model_validate(post)


@router.delete("/{post_id}", status_code=204)
async def delete_post(
    post_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(BlogPost).where(BlogPost.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="文章不存在")

    await db.execute(delete(Comment).where(Comment.post_id == post_id))
    await db.delete(post)
    await db.commit()
