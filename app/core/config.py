import secrets

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "cici-blog-backend"
    API_V1_PREFIX: str = "/api/v1"

    # Database - 必须通过环境变量设置
    DATABASE_URL: str = Field(default="", description="PostgreSQL database URL")

    # JWT - 必须通过环境变量设置，无默认值
    SECRET_KEY: str = Field(default="", description="JWT secret key")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_DAYS: int = 7

    # Admin whitelist (comma-separated emails or GitHub usernames)
    ADMIN_EMAILS: str = ""
    ADMIN_GITHUB_USERNAMES: str = ""

    # OAuth - Google
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # OAuth - GitHub
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""

    # Cloudflare R2
    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET_NAME: str = ""
    R2_CDN_URL: str = ""

    # AI / Agent
    TAVILY_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"

    # Environment
    ENVIRONMENT: str = "development"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        """验证 SECRET_KEY 在生产环境必须设置且足够安全。"""
        env = info.data.get("ENVIRONMENT", "development")
        if env == "production":
            if not v:
                raise ValueError("SECRET_KEY must be set in production environment")
            if len(v) < 32:
                raise ValueError("SECRET_KEY must be at least 32 characters in production")
        elif not v:
            # 开发环境自动生成临时密钥
            return secrets.token_urlsafe(32)
        return v

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str, info) -> str:
        """验证 DATABASE_URL 在生产环境必须设置。"""
        env = info.data.get("ENVIRONMENT", "development")
        if env == "production" and not v:
            raise ValueError("DATABASE_URL must be set in production environment")
        return v


settings = Settings()
