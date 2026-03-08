import datetime
import logging

from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_jwt_token(user_id: int, role: str) -> str:
    expire = datetime.datetime.now(datetime.UTC) + datetime.timedelta(
        days=settings.JWT_EXPIRE_DAYS
    )
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_jwt_token(token: str) -> dict | None:
    """解码 JWT 令牌，返回 payload 或 None（如果无效/过期）。"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except ExpiredSignatureError:
        logger.debug("JWT token expired")
        return None
    except JWTError as e:
        logger.debug(f"JWT token invalid: {e}")
        return None
    except Exception as e:
        logger.warning(f"Unexpected error decoding JWT token: {e}")
        return None
