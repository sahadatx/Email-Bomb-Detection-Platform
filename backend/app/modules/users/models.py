from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy import Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.base import UUIDTimestampMixin
from app.core.database import Base


class UserRole(str, Enum):
    """
    Roles available in the platform.
    """

    ADMIN = "ADMIN"
    SECURITY_ANALYST = "SECURITY_ANALYST"
    EMAIL_ANALYST = "EMAIL_ANALYST"
    VIEWER = "VIEWER"


class User(UUIDTimestampMixin, Base):
    """
    Platform user account.
    """

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
        index=True,
    )

    username: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    full_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    role: Mapped[UserRole] = mapped_column(
        SQLEnum(
            UserRole,
            name="user_role",
            native_enum=False,
        ),
        nullable=False,
        default=UserRole.VIEWER,
        index=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    is_locked: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    force_password_change: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    failed_login_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    locked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    sessions: Mapped[list["UserSession"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "email",
            name="uq_users_email",
        ),
        UniqueConstraint(
            "username",
            name="uq_users_username",
        ),
        Index(
            "ix_users_role_active",
            "role",
            "is_active",
        ),
    )


class UserSession(UUIDTimestampMixin, Base):
    """
    Authentication session associated with a user.
    """

    __tablename__ = "user_sessions"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    token_jti: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        unique=True,
        index=True,
    )

    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
    )

    user_agent: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    user: Mapped[User] = relationship(
        back_populates="sessions",
    )

    __table_args__ = (
        Index(
            "ix_user_sessions_user_active",
            "user_id",
            "revoked_at",
        ),
    )