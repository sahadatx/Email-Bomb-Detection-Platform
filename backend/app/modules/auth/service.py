from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import Request

from app.core.exceptions import AuthenticationError, ResourceNotFoundError
from app.core.security import (
    AccessToken,
    create_access_token,
    hash_password,
    is_session_active,
    verify_password,
)
from app.modules.auth.repository import AuthRepository
from app.modules.auth.schemas import (
    AuthenticatedUserResponse,
    SessionResponse,
    TokenResponse,
)
from app.modules.users.models import User
from app.modules.audit_security_admin.administration.settings_manager import get_effective_setting


MAX_FAILED_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_DURATION = timedelta(minutes=15)


class AuthService:
    """Application service for authentication and session management."""

    def __init__(self, repository: AuthRepository) -> None:
        self.repository = repository

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def login(
        self,
        *,
        email: str,
        password: str,
        request: Request,
    ) -> TokenResponse:
        normalized_email = email.strip().lower()

        user = self.repository.get_user_by_email(normalized_email)

        # Do not reveal whether the email exists.
        if user is None:
            raise AuthenticationError("Invalid email or password.")

        if not user.is_active:
            raise AuthenticationError("Account is disabled.")

        now = datetime.now(timezone.utc)
        if user.is_locked:
            expires_at = user.lockout_expires_at
            if expires_at is not None and expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at is None or expires_at > now:
                raise AuthenticationError("Account is locked.")

            # Failed-login lockouts are temporary. Administrative locks have
            # no expiry and therefore remain in force until explicitly lifted.
            user.is_locked = False
            user.failed_login_attempts = 0
            user.locked_at = None
            user.lockout_expires_at = None

        if not verify_password(password, user.password_hash):
            self._record_failed_login(user, now=now)

            self.repository.commit()

            raise AuthenticationError("Invalid email or password.")

        user.failed_login_attempts = 0
        user.last_login_at = now
        user.locked_at = None
        user.lockout_expires_at = None

        from app.core.config import settings as app_settings
        expires_minutes = get_effective_setting(self.repository.db, "security.session_timeout_minutes")
        access_token = create_access_token(
            user.id,
            expires_minutes=expires_minutes or app_settings.access_token_expire_minutes,
            claims={
                "role": user.role.value,
            },
        )

        self.repository.create_session(
            user_id=user.id,
            token_jti=access_token.jti,
            ip_address=self._get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
            expires_at=access_token.expires_at,
        )

        self.repository.commit()

        return TokenResponse(
            access_token=access_token.token,
            token_type="bearer",
            expires_at=access_token.expires_at,
        )

    def _record_failed_login(
        self, user: User, *, now: datetime | None = None
    ) -> None:
        user.failed_login_attempts += 1

        if user.failed_login_attempts >= MAX_FAILED_LOGIN_ATTEMPTS:
            now = now or datetime.now(timezone.utc)
            user.is_locked = True
            user.locked_at = now
            user.lockout_expires_at = now + LOGIN_LOCKOUT_DURATION

    # ------------------------------------------------------------------
    # Logout
    # ------------------------------------------------------------------

    def logout(self, *, token_jti: str) -> None:
        session = self.repository.get_session_by_jti(token_jti)

        if session is None:
            return

        if session.revoked_at is None:
            self.repository.revoke_session(
                session,
                revoked_at=datetime.now(timezone.utc),
            )

        self.repository.commit()

    # ------------------------------------------------------------------
    # Current user
    # ------------------------------------------------------------------

    def get_current_user(self, *, user_id: str) -> User:
        user = self.repository.get_user_by_id(user_id)

        if user is None:
            raise ResourceNotFoundError("Authenticated user was not found.")

        if not user.is_active:
            raise AuthenticationError("Account is disabled.")

        if user.is_locked:
            raise AuthenticationError("Account is locked.")

        return user

    def to_user_response(
        self,
        user: User,
    ) -> AuthenticatedUserResponse:
        return AuthenticatedUserResponse.model_validate(user)

    # ------------------------------------------------------------------
    # Sessions
    # ------------------------------------------------------------------

    def list_sessions(
        self,
        *,
        user_id: str,
    ) -> list[SessionResponse]:
        sessions = self.repository.list_user_sessions(
            user_id=user_id,
        )

        return [
            SessionResponse.model_validate(session)
            for session in sessions
        ]

    def revoke_session(
        self,
        *,
        user_id: str,
        session_id: str,
    ) -> None:
        session = self.repository.get_session_by_id(
            session_id=session_id,
            user_id=user_id,
        )

        if session is None:
            raise ResourceNotFoundError("Session was not found.")

        if session.revoked_at is None:
            self.repository.revoke_session(
                session,
                revoked_at=datetime.now(timezone.utc),
            )

        self.repository.commit()

    # ------------------------------------------------------------------
    # Session validation
    # ------------------------------------------------------------------

    def validate_session(
        self,
        *,
        user_id: str,
        token_jti: str,
    ) -> User:
        session = self.repository.get_session_by_jti(token_jti)

        if session is None:
            raise AuthenticationError("Authentication session was not found.")

        if session.user_id != user_id:
            raise AuthenticationError("Authentication session is invalid.")

        if not is_session_active(
            revoked_at=session.revoked_at,
            expires_at=session.expires_at,
        ):
            raise AuthenticationError("Authentication session is expired or revoked.")

        return self.get_current_user(user_id=user_id)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_client_ip(request: Request) -> str | None:
        if request.client is None:
            return None

        return request.client.host
