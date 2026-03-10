import logging

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
from datetime import datetime, timezone

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_jwt_token
from app.models.user import OAuthAccount, User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth/oauth", tags=["oauth"])

COOKIE_KEY = "access_token"


def _is_admin_email(email: str) -> bool:
    admin_emails = [e.strip() for e in settings.ADMIN_EMAILS.split(",") if e.strip()]
    return email in admin_emails


def _is_admin_github(username: str) -> bool:
    admin_usernames = [
        u.strip() for u in settings.ADMIN_GITHUB_USERNAMES.split(",") if u.strip()
    ]
    return username in admin_usernames


async def _find_or_create_user(
    db: AsyncSession,
    provider: str,
    provider_user_id: str,
    email: str,
    display_name: str,
    avatar_url: str | None,
    is_admin: bool,
) -> User:
    # 检查 OAuth 账号是否已存在
    result = await db.execute(
        select(OAuthAccount).where(
            OAuthAccount.provider == provider,
            OAuthAccount.provider_user_id == provider_user_id,
        )
    )
    oauth_account = result.scalar_one_or_none()

    if oauth_account:
        # Defensive handling for inconsistent data:
        # oauth account exists but linked user was manually deleted.
        result = await db.execute(select(User).where(User.id == oauth_account.user_id))
        linked_user = result.scalar_one_or_none()
        if linked_user:
            oauth_account.provider_email = email
            oauth_account.provider_display_name = display_name
            oauth_account.provider_avatar_url = avatar_url
            oauth_account.last_login_at = datetime.now(timezone.utc)
            linked_user.preferred_provider = provider
            # if not linked_user.display_name:
            #     linked_user.display_name = display_name
            if not linked_user.avatar_url:
                linked_user.avatar_url = avatar_url
            await db.commit()
            await db.refresh(linked_user)
            return linked_user
        await db.delete(oauth_account)
        await db.flush()

    # 检查相同邮箱的用户是否存在（账号关联）
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            email=email,
            avatar_url=avatar_url,
            preferred_provider=provider,
            role="admin" if is_admin else "visitor",
        )
        db.add(user)
        await db.flush()
    else:
        user.preferred_provider = provider
        if not user.display_name:
            user.display_name = display_name
        if not user.avatar_url:
            user.avatar_url = avatar_url

    # 关联 OAuth 账号
    result = await db.execute(
        select(OAuthAccount).where(
            OAuthAccount.user_id == user.id,
            OAuthAccount.provider == provider,
        )
    )
    existing_link = result.scalar_one_or_none()

    if existing_link:
        existing_link.provider_user_id = provider_user_id
        existing_link.provider_email = email
        existing_link.provider_display_name = display_name
        existing_link.provider_avatar_url = avatar_url
        existing_link.last_login_at = datetime.now(timezone.utc)
    else:
        oauth_account = OAuthAccount(
            user_id=user.id,
            provider=provider,
            provider_user_id=provider_user_id,
            provider_email=email,
            provider_display_name=display_name,
            provider_avatar_url=avatar_url,
            last_login_at=datetime.now(timezone.utc),
        )
        db.add(oauth_account)
    await db.commit()
    await db.refresh(user)
    return user


def _set_auth_cookie(response: Response, user: User) -> None:
    token = create_jwt_token(user.id, user.role)
    response.set_cookie(
        key=COOKIE_KEY,
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7 * 24 * 3600,
    )


# --- Google OAuth ---


@router.get("/google/url")
async def google_auth_url():
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=501, detail="Google OAuth 未配置")
    redirect_uri = f"{settings.CORS_ORIGINS.split(',')[0]}/auth/google/callback"
    url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={settings.GOOGLE_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        "&response_type=code"
        "&scope=openid+email+profile"
        "&access_type=offline"
    )
    return {"url": url}


@router.post("/google/callback")
async def google_callback(
    code: str,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    redirect_uri = f"{settings.CORS_ORIGINS.split(',')[0]}/auth/google/callback"

    async with httpx.AsyncClient() as client:
        # 用授权码换取令牌
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if token_resp.status_code != 200:
            logger.error(f"Google token exchange failed: {token_resp.status_code}")
            raise HTTPException(status_code=400, detail="Google 授权失败")

        try:
            tokens = token_resp.json()
        except Exception as e:
            logger.error(f"Failed to parse Google token response: {e}")
            raise HTTPException(status_code=500, detail="Google 授权响应解析失败")

        access_token = tokens.get("access_token")
        if not access_token:
            logger.error("Google token response missing access_token")
            raise HTTPException(status_code=400, detail="Google 授权失败")

        # 获取用户信息
        userinfo_resp = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if userinfo_resp.status_code != 200:
            logger.error(f"Google userinfo fetch failed: {userinfo_resp.status_code}")
            raise HTTPException(status_code=400, detail="获取 Google 用户信息失败")

        try:
            userinfo = userinfo_resp.json()
        except Exception as e:
            logger.error(f"Failed to parse Google userinfo response: {e}")
            raise HTTPException(status_code=500, detail="Google 用户信息解析失败")

    email = userinfo.get("email", "")
    user = await _find_or_create_user(
        db=db,
        provider="google",
        provider_user_id=str(userinfo["id"]),
        email=email,
        display_name=userinfo.get("name", email.split("@")[0]),
        avatar_url=userinfo.get("picture"),
        is_admin=_is_admin_email(email),
    )
    _set_auth_cookie(response, user)
    return {"message": "Google 登录成功", "user_id": user.id, "role": user.role}


# --- GitHub OAuth ---


@router.get("/github/url")
async def github_auth_url():
    if not settings.GITHUB_CLIENT_ID:
        raise HTTPException(status_code=501, detail="GitHub OAuth 未配置")
    redirect_uri = f"{settings.CORS_ORIGINS.split(',')[0]}/auth/github/callback"
    url = (
        "https://github.com/login/oauth/authorize"
        f"?client_id={settings.GITHUB_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        "&scope=user:email"
    )
    return {"url": url}


@router.post("/github/callback")
async def github_callback(
    code: str,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    async with httpx.AsyncClient() as client:
        # 用授权码换取令牌
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            json={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )
        if token_resp.status_code != 200:
            logger.error(f"GitHub token exchange failed: {token_resp.status_code}")
            raise HTTPException(status_code=400, detail="GitHub 授权失败")

        try:
            tokens = token_resp.json()
        except Exception as e:
            logger.error(f"Failed to parse GitHub token response: {e}")
            raise HTTPException(status_code=500, detail="GitHub 授权响应解析失败")

        access_token = tokens.get("access_token")
        if not access_token:
            logger.error("GitHub token response missing access_token")
            raise HTTPException(status_code=400, detail="GitHub 授权失败")

        # 获取用户信息
        user_resp = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if user_resp.status_code != 200:
            logger.error(f"GitHub user fetch failed: {user_resp.status_code}")
            raise HTTPException(status_code=400, detail="获取 GitHub 用户信息失败")

        try:
            github_user = user_resp.json()
        except Exception as e:
            logger.error(f"Failed to parse GitHub user response: {e}")
            raise HTTPException(status_code=500, detail="GitHub 用户信息解析失败")

        # 获取主邮箱
        email_resp = await client.get(
            "https://api.github.com/user/emails",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        primary_email = ""
        if email_resp.status_code == 200:
            try:
                emails = email_resp.json()
                primary_email = next(
                    (e["email"] for e in emails if e.get("primary")),
                    github_user.get("email", ""),
                )
            except Exception as e:
                logger.warning(f"Failed to parse GitHub emails response: {e}")
                primary_email = github_user.get("email", "")
        else:
            primary_email = github_user.get("email", "")

    github_username = github_user.get("login", "")
    is_admin = _is_admin_email(primary_email) or _is_admin_github(github_username)

    user = await _find_or_create_user(
        db=db,
        provider="github",
        provider_user_id=str(github_user["id"]),
        email=primary_email,
        display_name=github_user.get("name") or github_username,
        avatar_url=github_user.get("avatar_url"),
        is_admin=is_admin,
    )
    _set_auth_cookie(response, user)
    return {"message": "GitHub 登录成功", "user_id": user.id, "role": user.role}
