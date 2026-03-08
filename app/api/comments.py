import re
from collections import defaultdict
from time import time

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user_optional, require_admin
from app.models.blog import BlogPost, Comment
from app.models.user import User
from app.schemas.comment import (
    CommentApproveRequest,
    CommentCreate,
    CommentListResponse,
    CommentResponse,
)

router = APIRouter(tags=["comments"])

# 评论的内存限流器
_comment_timestamps: dict[str, list[float]] = defaultdict(list)
COMMENT_RATE_WINDOW = 60  # 1 minute
COMMENT_RATE_LIMIT = 3

# 垃圾评论过滤的敏感词列表。
SENSITIVE_WORDS: list[str] = []


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _check_comment_rate(ip: str) -> bool:
    now = time()
    timestamps = _comment_timestamps[ip]
    # Remove expired entries
    _comment_timestamps[ip] = [t for t in timestamps if now - t < COMMENT_RATE_WINDOW]
    return len(_comment_timestamps[ip]) >= COMMENT_RATE_LIMIT


def _is_spam(content: str) -> bool:
    # Check external links count
    urls = re.findall(r"https?://", content)
    if len(urls) > 5:
        return True
    # Check sensitive words
    lower_content = content.lower()
    for word in SENSITIVE_WORDS:
        if word.lower() in lower_content:
            return True
    return False


def _validate_email(email: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))


# --- 公共端点 ---


@router.post("/posts/{post_id}/comments", response_model=CommentResponse, status_code=201)
async def create_comment(
    post_id: int,
    data: CommentCreate,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    # Rate limit check
    client_ip = _get_client_ip(request)
    if _check_comment_rate(client_ip):
        raise HTTPException(status_code=429, detail="操作过于频繁，请稍后再试")

    # Verify post exists
    result = await db.execute(select(BlogPost).where(BlogPost.id == post_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="文章不存在")

    # Check if user is logged in
    user = await get_current_user_optional(request, response, db)

    if user:
        author_name = user.display_name
        author_email = user.email
        user_id = user.id
    else:
        # Validate required fields for anonymous users
        if not data.author_name or not data.author_name.strip():
            raise HTTPException(status_code=400, detail="昵称不能为空")
        if not data.author_email or not _validate_email(data.author_email):
            raise HTTPException(status_code=400, detail="请输入有效的邮箱地址")
        author_name = data.author_name.strip()
        author_email = data.author_email.strip()
        user_id = None

    # Spam check
    is_spam = _is_spam(data.content)

    comment = Comment(
        post_id=post_id,
        user_id=user_id,
        author_name=author_name,
        author_email=author_email,
        content=data.content,
        is_approved=not is_spam and user is not None and user.role == "admin",
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)

    # Record rate limit
    _comment_timestamps[client_ip].append(time())

    return CommentResponse.model_validate(comment)


@router.get("/posts/{post_id}/comments", response_model=list[CommentResponse])
async def list_post_comments(
    post_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Comment)
        .where(Comment.post_id == post_id, Comment.is_approved == True)
        .order_by(Comment.created_at.asc())
    )
    comments = result.scalars().all()
    return [CommentResponse.model_validate(c) for c in comments]


# --- 管理端点 ---


@router.get("/admin/comments", response_model=CommentListResponse)
async def admin_list_comments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_approved: bool | None = None,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    query = select(Comment)
    if is_approved is not None:
        query = query.where(Comment.is_approved == is_approved)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(Comment.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    comments = result.scalars().all()

    return CommentListResponse(
        items=[CommentResponse.model_validate(c) for c in comments],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.put("/admin/comments/{comment_id}", response_model=CommentResponse)
async def admin_update_comment(
    comment_id: int,
    data: CommentApproveRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")

    comment.is_approved = data.is_approved
    await db.commit()
    await db.refresh(comment)
    return CommentResponse.model_validate(comment)


@router.delete("/admin/comments/{comment_id}", status_code=204)
async def admin_delete_comment(
    comment_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")

    await db.delete(comment)
    await db.commit()
