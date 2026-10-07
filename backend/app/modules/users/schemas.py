from __future__ import annotations

from datetime import datetime

from pydantic import EmailStr, Field

from app.common.pagination import PaginationParams
from app.common.schemas import APIModel
from app.modules.users.models import UserRole


# ---------------------------------------------------------------------------
# User responses
# ---------------------------------------------------------------------------

class UserSummaryResponse(APIModel):
    id: str
    email: EmailStr
    username: str
    full_name: str
    role: UserRole
    is_active: bool
    is_locked: bool
    force_password_change: bool
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime


class UserDetailResponse(UserSummaryResponse):
    failed_login_attempts: int
    locked_at: datetime | None


class UserSessionResponse(APIModel):
    id: str
    token_jti: str
    ip_address: str | None
    user_agent: str | None
    expires_at: datetime
    revoked_at: datetime | None
    created_at: datetime


class ManagedUserSessionResponse(APIModel):
    """Safe session representation for privileged account management."""
    id: str
    ip_address: str | None
    user_agent: str | None
    expires_at: datetime
    revoked_at: datetime | None
    created_at: datetime


# ---------------------------------------------------------------------------
# User creation
# ---------------------------------------------------------------------------

class CreateUserRequest(APIModel):
    email: EmailStr
    username: str = Field(
        min_length=3,
        max_length=100,
    )
    full_name: str = Field(
        min_length=1,
        max_length=200,
    )
    password: str = Field(
        min_length=12,
        max_length=128,
    )
    role: UserRole = UserRole.VIEWER
    is_active: bool = True
    force_password_change: bool = False


# ---------------------------------------------------------------------------
# User update
# ---------------------------------------------------------------------------

class UpdateUserRequest(APIModel):
    email: EmailStr | None = None
    username: str | None = Field(
        default=None,
        min_length=3,
        max_length=100,
    )
    full_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )


class ChangeRoleRequest(APIModel):
    role: UserRole


class ChangePasswordRequest(APIModel):
    current_password: str = Field(
        min_length=1,
        max_length=128,
    )
    new_password: str = Field(
        min_length=12,
        max_length=128,
    )


class ResetPasswordRequest(APIModel):
    new_password: str = Field(
        min_length=12,
        max_length=128,
    )


class ForcePasswordChangeRequest(APIModel):
    force_password_change: bool


# ---------------------------------------------------------------------------
# User list
# ---------------------------------------------------------------------------

class UserListParams(PaginationParams):
    search: str | None = Field(
        default=None,
        max_length=200,
    )
    role: UserRole | None = None
    is_active: bool | None = None
    is_locked: bool | None = None


class UserListResponse(APIModel):
    items: list[UserSummaryResponse]
    page: int
    page_size: int
    total: int
    pages: int


class UserCountsResponse(APIModel):
    total: int
    active: int
    disabled: int
    locked: int
