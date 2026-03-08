from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rate_limit import login_rate_limiter
from app.core.security import create_jwt_token, hash_password, verify_password
from app.models.user import OAuthAccount, User
from app.schemas.auth import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])

COOKIE_KEY = "access_token"


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    client_ip = _get_client_ip(request)

    if login_rate_limiter.is_locked(client_ip):
        raise HTTPException(status_code=429, detail="登录尝试过多，请稍后再试")

    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not user.password_hash:
        login_rate_limiter.record_failure(client_ip)
        raise HTTPException(status_code=401, detail="邮箱或密码错误")

    if not verify_password(data.password, user.password_hash):
        login_rate_limiter.record_failure(client_ip)
        raise HTTPException(status_code=401, detail="邮箱或密码错误")

    login_rate_limiter.reset(client_ip)
    token = create_jwt_token(user.id, user.role)
    response.set_cookie(
        key=COOKIE_KEY,
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7 * 24 * 3600,
    )
    return TokenResponse(message="登录成功", user_id=user.id, role=user.role)


@router.post("/register", response_model=TokenResponse)
async def register(
    data: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该邮箱已注册")

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        display_name=data.email.split("@")[0],
        role="visitor",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_jwt_token(user.id, user.role)
    response.set_cookie(
        key=COOKIE_KEY,
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7 * 24 * 3600,
    )
    return TokenResponse(message="注册成功", user_id=user.id, role=user.role)


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key=COOKIE_KEY, httponly=True, secure=True, samesite="lax")
    return {"message": "已退出登录"}


@router.get("/me")
async def get_me(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    from app.core.deps import get_current_user_optional

    user = await get_current_user_optional(request, response, db)
    if not user:
        return {"user": None}

    display_name = ""
    avatar_url = user.avatar_url
    if user.preferred_provider:
        oauth_result = await db.execute(
            select(OAuthAccount).where(
                OAuthAccount.user_id == user.id,
                OAuthAccount.provider == user.preferred_provider,
            )
        )
        preferred_profile = oauth_result.scalar_one_or_none()
        if preferred_profile:
            display_name = preferred_profile.provider_display_name
            avatar_url = preferred_profile.provider_avatar_url

    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "display_name": display_name,
            "avatar_url": avatar_url,
            "role": user.role,
            "preferred_provider": user.preferred_provider,
        }
    }
