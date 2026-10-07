from datetime import datetime

from pydantic import EmailStr, Field

from app.common.schemas import APIModel
from app.modules.users.models import UserRole


class LoginRequest(APIModel):
    """
    Credentials submitted during authentication.
    """

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(APIModel):
    """
    Authentication token returned after successful login.
    """

    access_token: str
    token_type: str = "bearer"
    expires_at: datetime


class AuthenticatedUserResponse(APIModel):
    """
    Public representation of the authenticated user.
    """

    id: str
    email: EmailStr
    username: str
    full_name: str
    role: UserRole
    is_active: bool
    is_locked: bool
    force_password_change: bool


class SessionResponse(APIModel):
    """
    Public representation of a server-side authentication session.
    """

    id: str
    token_jti: str
    ip_address: str | None
    user_agent: str | None
    expires_at: datetime
    revoked_at: datetime | None
    created_at: datetime