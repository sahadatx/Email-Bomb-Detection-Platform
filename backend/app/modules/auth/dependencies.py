from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.common.dependencies import database_session
from app.core.exceptions import AuthenticationError
from app.core.security import decode_access_token
from app.modules.auth.repository import AuthRepository
from app.modules.auth.service import AuthService
from app.modules.users.models import User


# ---------------------------------------------------------------------------
# HTTP authentication scheme
# ---------------------------------------------------------------------------

bearer_scheme = HTTPBearer(
    auto_error=False,
)


# ---------------------------------------------------------------------------
# Authentication service dependency
# ---------------------------------------------------------------------------

def get_auth_service(
    db: Annotated[Session, Depends(database_session)],
) -> AuthService:
    """
    Provide an AuthService instance backed by the current database session.
    """
    repository = AuthRepository(db)

    return AuthService(repository)


# ---------------------------------------------------------------------------
# Access-token dependency
# ---------------------------------------------------------------------------

def get_current_access_token(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
) -> str:
    """
    Extract the Bearer access token from the Authorization header.

    Expected header:

        Authorization: Bearer <token>
    """
    if credentials is None:
        raise AuthenticationError(
            "Authentication credentials are required."
        )

    if credentials.scheme.lower() != "bearer":
        raise AuthenticationError(
            "Bearer authentication is required."
        )

    if not credentials.credentials:
        raise AuthenticationError(
            "Access token is required."
        )

    return credentials.credentials


# ---------------------------------------------------------------------------
# Current authenticated user
# ---------------------------------------------------------------------------

def get_current_authenticated_user(
    token: Annotated[
        str,
        Depends(get_current_access_token),
    ],
    service: Annotated[
        AuthService,
        Depends(get_auth_service),
    ],
) -> User:
    """
    Authenticate the current request and return the authenticated User.

    Authentication requires both:

    1. A cryptographically valid JWT.
    2. A valid, active server-side UserSession.
    """
    try:
        payload = decode_access_token(token)
    except Exception as exc:
        raise AuthenticationError(
            "Invalid or expired access token."
        ) from exc

    user_id = payload.get("sub")
    token_jti = payload.get("jti")

    if not user_id:
        raise AuthenticationError(
            "Access token subject is missing."
        )

    if not token_jti:
        raise AuthenticationError(
            "Access token session identifier is missing."
        )

    return service.validate_session(
        user_id=str(user_id),
        token_jti=str(token_jti),
    )