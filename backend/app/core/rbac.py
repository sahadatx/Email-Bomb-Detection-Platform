from __future__ import annotations

from collections.abc import Iterable
from typing import Annotated

from fastapi import Depends, Request

from app.core.exceptions import AuthorizationError
from app.core.permissions import Permission
from app.modules.auth.dependencies import get_current_authenticated_user
from app.modules.users.models import User, UserRole


ROLE_PERMISSIONS: dict[UserRole, frozenset[Permission]] = {
    UserRole.ADMIN: frozenset(Permission),

    UserRole.SECURITY_ANALYST: frozenset(
        {
            Permission.PROFILE_READ,
            Permission.PROFILE_PASSWORD_CHANGE,
            Permission.PROFILE_SESSIONS_READ,
            Permission.PROFILE_SESSION_REVOKE,

            Permission.EMAILS_READ,
            Permission.EMAILS_INGEST,

            Permission.INVESTIGATION_READ,
            Permission.INVESTIGATION_NOTE_CREATE,
            Permission.INVESTIGATION_NOTE_UPDATE,
            Permission.INVESTIGATION_NOTE_DELETE,
            Permission.EVIDENCE_CREATE,
            Permission.EVIDENCE_READ,
            Permission.EVIDENCE_UPDATE,
            Permission.EVIDENCE_REVIEW,
            Permission.EVIDENCE_EXPORT,
            Permission.REPORT_CREATE,
            Permission.REPORT_GENERATE,
            Permission.REPORT_DOWNLOAD,

            Permission.SECURITY_EVENTS_READ,
            Permission.SECURITY_ALERTS_READ,
            Permission.MONITORING_RULES_READ,
            Permission.ANALYTICS_READ,
            Permission.ANALYTICS_EXPORT,
            Permission.EXPERIMENTS_READ,
            Permission.EXPERIMENTS_MANAGE,
            Permission.THREAT_INTELLIGENCE_READ,
            Permission.THREAT_INTELLIGENCE_EXPORT,
            Permission.THREAT_INDICATORS_MANAGE,
            Permission.THREAT_FEEDS_MANAGE,
            Permission.THREAT_MATCHES_INVESTIGATE,
        }
    ),

    UserRole.EMAIL_ANALYST: frozenset(
        {
            Permission.PROFILE_READ,
            Permission.PROFILE_PASSWORD_CHANGE,
            Permission.PROFILE_SESSIONS_READ,
            Permission.PROFILE_SESSION_REVOKE,
            Permission.EMAILS_READ,
            Permission.EMAILS_INGEST,
            Permission.INVESTIGATION_READ,
            Permission.EVIDENCE_READ,
            Permission.REPORT_DOWNLOAD,
            Permission.ANALYTICS_READ,
            Permission.THREAT_INTELLIGENCE_READ,
        }
    ),

    UserRole.VIEWER: frozenset(
        {
            Permission.PROFILE_READ,
            Permission.PROFILE_PASSWORD_CHANGE,
            Permission.PROFILE_SESSIONS_READ,
            Permission.PROFILE_SESSION_REVOKE,
            Permission.EMAILS_READ,
            Permission.INVESTIGATION_READ,
            Permission.REPORT_DOWNLOAD,
            Permission.ANALYTICS_READ,
            Permission.THREAT_INTELLIGENCE_READ,
        }
    ),
}


def get_role_permissions(role: UserRole) -> frozenset[Permission]:
    try:
        return ROLE_PERMISSIONS[role]
    except KeyError as exc:
        raise AuthorizationError(
            f"No RBAC policy is defined for role '{role}'."
        ) from exc


def has_permission(
    user: User,
    permission: Permission,
) -> bool:
    return permission in get_role_permissions(user.role)


def has_any_permission(
    user: User,
    permissions: Iterable[Permission],
) -> bool:
    user_permissions = get_role_permissions(user.role)
    return any(
        permission in user_permissions
        for permission in permissions
    )


def has_all_permissions(
    user: User,
    permissions: Iterable[Permission],
) -> bool:
    user_permissions = get_role_permissions(user.role)
    return all(
        permission in user_permissions
        for permission in permissions
    )


def require_role(*allowed_roles: UserRole):
    allowed = frozenset(allowed_roles)

    if not allowed:
        raise ValueError(
            "At least one allowed role must be specified."
        )

    def dependency(
        current_user: Annotated[
            User,
            Depends(get_current_authenticated_user),
        ],
    ) -> User:
        if current_user.role not in allowed:
            allowed_names = ", ".join(
                role.value
                for role in sorted(
                    allowed,
                    key=lambda item: item.value,
                )
            )

            raise AuthorizationError(
                f"Required role: {allowed_names}."
            )

        return current_user

    return dependency


def require_permission(*required_permissions: Permission):
    required = frozenset(required_permissions)

    if not required:
        raise ValueError(
            "At least one permission must be specified."
        )

    def dependency(
        current_user: Annotated[
            User,
            Depends(get_current_authenticated_user),
        ],
    ) -> User:
        user_permissions = get_role_permissions(
            current_user.role
        )

        missing_permissions = [
            permission
            for permission in required
            if permission not in user_permissions
        ]

        if missing_permissions:
            missing = ", ".join(
                permission.value
                for permission in sorted(
                    missing_permissions,
                    key=lambda item: item.value,
                )
            )

            raise AuthorizationError(
                f"Missing required permission: {missing}."
            )

        return current_user

    return dependency


def require_any_permission(*required_permissions: Permission):
    required = frozenset(required_permissions)

    if not required:
        raise ValueError(
            "At least one permission must be specified."
        )

    def dependency(
        current_user: Annotated[
            User,
            Depends(get_current_authenticated_user),
        ],
    ) -> User:
        user_permissions = get_role_permissions(
            current_user.role
        )

        if not any(
            permission in user_permissions
            for permission in required
        ):
            required_names = ", ".join(
                permission.value
                for permission in sorted(
                    required,
                    key=lambda item: item.value,
                )
            )

            raise AuthorizationError(
                "At least one required permission is needed: "
                f"{required_names}."
            )

        return current_user

    return dependency


def require_module_access(module: str):
    """Protect legacy module routers using the application's role matrix."""
    def dependency(
        request: Request,
        current_user: Annotated[User, Depends(get_current_authenticated_user)],
    ) -> User:
        role = current_user.role
        method = request.method.upper()
        path = request.url.path
        read_roles = {UserRole.ADMIN, UserRole.SECURITY_ANALYST, UserRole.EMAIL_ANALYST, UserRole.VIEWER}
        manage_roles = {UserRole.ADMIN, UserRole.SECURITY_ANALYST, UserRole.EMAIL_ANALYST}
        if module == "models":
            read_roles = {UserRole.ADMIN, UserRole.SECURITY_ANALYST, UserRole.VIEWER}
            if "/training-runs" in path:
                read_roles = {UserRole.ADMIN, UserRole.SECURITY_ANALYST}
            elif "/evaluation" in path:
                read_roles.add(UserRole.EMAIL_ANALYST)
            manage_roles = {UserRole.ADMIN, UserRole.SECURITY_ANALYST}
        elif module == "detection":
            manage_roles = {UserRole.ADMIN, UserRole.SECURITY_ANALYST, UserRole.EMAIL_ANALYST}
            if "/settings" in path:
                read_roles = manage_roles = {UserRole.ADMIN}
        allowed = read_roles if method in {"GET", "HEAD", "OPTIONS"} else manage_roles
        if role not in allowed:
            raise AuthorizationError(f"Role '{role.value}' cannot access the {module} module.")
        return current_user
    return dependency


def get_current_user_with_permission(
    permission: Permission,
):
    return require_permission(permission)


def get_current_user_with_role(
    *roles: UserRole,
):
    return require_role(*roles)
