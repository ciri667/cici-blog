import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    # display_name: Mapped[str] = mapped_column(String(100))
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    preferred_provider: Mapped[str | None] = mapped_column(String(20))
    role: Mapped[str] = mapped_column(String(20), default="visitor")  # admin / visitor
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class OAuthAccount(Base):
    __tablename__ = "oauth_accounts"
    __table_args__ = (
        UniqueConstraint("provider", "provider_user_id", name="uq_oauth_provider_user"),
        UniqueConstraint("user_id", "provider", name="uq_oauth_user_provider"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(index=True)
    provider: Mapped[str] = mapped_column(String(20))  # google / github
    provider_user_id: Mapped[str] = mapped_column(String(255))
    provider_email: Mapped[str | None] = mapped_column(String(255))
    provider_display_name: Mapped[str | None] = mapped_column(String(100))
    provider_avatar_url: Mapped[str | None] = mapped_column(String(500))
    access_token: Mapped[str | None] = mapped_column(String(500))
    last_login_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
