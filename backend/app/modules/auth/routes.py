from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from app.modules.auth.dependencies import (
    get_auth_service,
    get_current_access_token,
    get_current_authenticated_user,
)
from app.modules.auth.schemas import (
    AuthenticatedUserResponse,
    LoginRequest,
    SessionResponse,
    TokenResponse,
)
from app.modules.auth.service import AuthService
from app.modules.users.models import User
from app.modules.audit_security_admin.audit.service import record_audit
from app.core.exceptions import AuthenticationError


router = APIRouter()


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate a user",
    description="Authenticate a user and create a server-side session.",
)
def login(
    payload: LoginRequest,
    request: Request,
    service: Annotated[
        AuthService,
        Depends(get_auth_service),
    ],
) -> TokenResponse:
    """
    Authenticate a user using email and password.

    A successful login creates:

    1. A signed JWT access token.
    2. A corresponding server-side UserSession.
    """
    try:
        result = service.login(email=str(payload.email), password=payload.password, request=request)
    except AuthenticationError:
        actor = service.repository.get_user_by_email(str(payload.email).strip().lower())
        details = {"reason": "Authentication was rejected."}
        source_ip = request.client.host if request.client else None
        record_audit(service.repository.db, actor=actor, action="auth.login_failed", status="failure", severity="high", source="Authentication", ip_address=source_ip, details=details)
        from app.modules.audit_security_admin.security_monitoring.event_processor import process_security_event
        process_security_event(service.repository.db, {"event_type": "auth.login_failed", "title": "Failed authentication attempt", "description": "A login request was rejected.", "severity": "high", "source": "Authentication", "actor_id": actor.id if actor else None, "source_ip": source_ip, "details": details})
        service.repository.commit()
        raise
    actor = service.repository.get_user_by_email(str(payload.email).strip().lower())
    record_audit(service.repository.db, actor=actor, action="auth.login_succeeded", source="Authentication", ip_address=request.client.host if request.client else None)
    service.repository.commit()
    return result


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout current session",
    description="Revoke the current authenticated session.",
)
def logout(
    token: Annotated[
        str,
        Depends(get_current_access_token),
    ],
    service: Annotated[
        AuthService,
        Depends(get_auth_service),
    ],
    current_user: Annotated[User, Depends(get_current_authenticated_user)],
) -> None:
    """
    Revoke the current access-token session.
    """
    from app.core.security import get_token_jti

    try:
        token_jti = get_token_jti(token)
    except Exception:
        # The authentication dependency already validates the token.
        # This is a defensive guard for direct dependency invocation.
        return

    service.logout(token_jti=token_jti)
    record_audit(service.repository.db, actor=current_user, action="auth.logout", source="Authentication")
    service.repository.commit()


# ---------------------------------------------------------------------------
# Current user
# ---------------------------------------------------------------------------

@router.get(
    "/me",
    response_model=AuthenticatedUserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user",
)
def get_me(
    current_user: Annotated[
        User,
        Depends(get_current_authenticated_user),
    ],
) -> AuthenticatedUserResponse:
    """
    Return the currently authenticated user.
    """
    return AuthenticatedUserResponse.model_validate(current_user)


# ---------------------------------------------------------------------------
# Session management
# ---------------------------------------------------------------------------

@router.get(
    "/sessions",
    response_model=list[SessionResponse],
    status_code=status.HTTP_200_OK,
    summary="List current user's sessions",
)
def list_sessions(
    current_user: Annotated[
        User,
        Depends(get_current_authenticated_user),
    ],
    service: Annotated[
        AuthService,
        Depends(get_auth_service),
    ],
) -> list[SessionResponse]:
    """
    Return all sessions belonging to the authenticated user.
    """
    return service.list_sessions(
        user_id=current_user.id,
    )


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke a user session",
)
def revoke_session(
    session_id: str,
    current_user: Annotated[
        User,
        Depends(get_current_authenticated_user),
    ],
    service: Annotated[
        AuthService,
        Depends(get_auth_service),
    ],
) -> None:
    """
    Revoke one session belonging to the authenticated user.
    """
    service.revoke_session(
        user_id=current_user.id,
        session_id=session_id,
    )
