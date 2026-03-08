from fastapi import Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_jwt_token, decode_jwt_token
from app.models.user import User

COOKIE_KEY = "access_token"


async def get_current_user(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> User:
    token = request.cookies.get(COOKIE_KEY)
    if not token:
        raise HTTPException(status_code=401, detail="未登录")

    payload = decode_jwt_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="会话已过期，请重新登录")

    user_id = int(payload["sub"])
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")

    # 滑动过期：每次请求刷新令牌
    new_token = create_jwt_token(user.id, user.role)
    response.set_cookie(
        key=COOKIE_KEY,
        value=new_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=settings.JWT_EXPIRE_DAYS * 24 * 3600,
    )

    return user


async def get_current_user_optional(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> User | None:
    token = request.cookies.get(COOKIE_KEY)
    if not token:
        return None

    payload = decode_jwt_token(token)
    if not payload:
        return None

    user_id = int(payload["sub"])
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def require_admin(
    user: User = Depends(get_current_user),
) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user
