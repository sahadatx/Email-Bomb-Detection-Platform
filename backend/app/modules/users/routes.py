from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.common.dependencies import database_session
from app.core.permissions import Permission
from app.core.rbac import require_permission
from app.modules.auth.dependencies import get_current_authenticated_user
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import (
    ChangePasswordRequest,
    ChangeRoleRequest,
    CreateUserRequest,
    ForcePasswordChangeRequest,
    ResetPasswordRequest,
    UpdateUserRequest,
    UserDetailResponse,
    UserCountsResponse,
    UserListParams,
    UserListResponse,
    UserSummaryResponse,
    UserSessionResponse,
    ManagedUserSessionResponse,
)
from app.modules.users.service import UserService
from app.modules.audit_security_admin.audit.service import record_audit


router = APIRouter()


def get_user_service(
    db=Depends(database_session),
) -> UserService:
    return UserService(UserRepository(db))


CurrentUser = Annotated[
    User,
    Depends(get_current_authenticated_user),
]

AdminUser = Annotated[
    User,
    Depends(require_permission(Permission.USERS_READ)),
]


def record_admin_action(service: UserService, actor: User, action: str, target: User) -> None:
    db = service.repository.db
    record_audit(db, actor=actor, action=action, target_type="user", target_id=target.id, target_label=target.username, source="User Management")
    if action in {"user.disabled", "user.locked", "user.role_changed", "user.password_reset"}:
        from app.modules.audit_security_admin.security_monitoring.event_processor import process_security_event
        process_security_event(db, {"event_type": action, "title": action.replace(".", " ").replace("_", " ").title(), "description": "A privileged user-management action was performed.", "severity": "high" if action in {"user.role_changed", "user.password_reset"} else "medium", "source": "User Management", "actor_id": actor.id, "details": {"target_user_id": target.id}} , actor=actor)
    db.commit()


@router.get(
    "/me",
    response_model=UserDetailResponse,
    summary="Get own user profile",
)
def get_my_profile(
    current_user: CurrentUser,
) -> UserDetailResponse:
    return UserDetailResponse.model_validate(current_user)


@router.post(
    "/me/password",
    response_model=UserDetailResponse,
    summary="Change own password",
)
def change_my_password(
    payload: ChangePasswordRequest,
    current_user: CurrentUser,
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserDetailResponse:
    user = service.change_own_password(
        user=current_user,
        payload=payload,
    )
    record_admin_action(service, current_user, "user.password_changed", current_user)
    return UserDetailResponse.model_validate(user)


@router.get(
    "",
    response_model=UserListResponse,
    summary="List users",
)
def list_users(
    current_user: AdminUser,
    service: Annotated[UserService, Depends(get_user_service)],
    params: Annotated[UserListParams, Depends()],
) -> UserListResponse:
    return service.list_users(params)


@router.get(
    "/summary",
    response_model=UserCountsResponse,
    summary="Get global user account counts",
)
def user_summary(
    current_user: AdminUser,
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserCountsResponse:
    return UserCountsResponse(**service.summary())


@router.get("/{user_id}/sessions", response_model=list[ManagedUserSessionResponse])
def list_user_sessions(
    user_id: str,
    current_user: Annotated[User, Depends(require_permission(Permission.USERS_READ))],
    service: Annotated[UserService, Depends(get_user_service)],
):
    return [ManagedUserSessionResponse.model_validate(item) for item in service.list_sessions(user_id)]


@router.delete("/{user_id}/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_user_session(
    user_id: str,
    session_id: str,
    current_user: Annotated[User, Depends(require_permission(Permission.USERS_UPDATE))],
    service: Annotated[UserService, Depends(get_user_service)],
):
    service.revoke_session(user_id, session_id)
    record_audit(service.repository.db, actor=current_user, action="user.session_revoked", target_type="user", target_id=user_id, target_label=user_id, source="User Management")
    service.repository.commit()


@router.delete("/{user_id}/sessions", status_code=status.HTTP_200_OK)
def revoke_all_user_sessions(
    user_id: str,
    current_user: Annotated[User, Depends(require_permission(Permission.USERS_UPDATE))],
    service: Annotated[UserService, Depends(get_user_service)],
):
    count = service.revoke_all_sessions(user_id)
    record_audit(service.repository.db, actor=current_user, action="user.sessions_revoked", target_type="user", target_id=user_id, target_label=user_id, source="User Management")
    service.repository.commit()
    return {"revoked_count": count}


@router.post(
    "",
    response_model=UserDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create user",
)
def create_user(
    payload: CreateUserRequest,
    current_user: Annotated[
        User,
        Depends(require_permission(Permission.USERS_CREATE)),
    ],
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserDetailResponse:
    user = service.create_user(payload)
    record_admin_action(service, current_user, "user.created", user)
    return UserDetailResponse.model_validate(user)


@router.get(
    "/{user_id}",
    response_model=UserDetailResponse,
    summary="Get user details",
)
def get_user(
    user_id: str,
    current_user: Annotated[
        User,
        Depends(require_permission(Permission.USERS_READ)),
    ],
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserDetailResponse:
    user = service.get_user(user_id)
    return UserDetailResponse.model_validate(user)


@router.patch(
    "/{user_id}",
    response_model=UserDetailResponse,
    summary="Update user",
)
def update_user(
    user_id: str,
    payload: UpdateUserRequest,
    current_user: Annotated[
        User,
        Depends(require_permission(Permission.USERS_UPDATE)),
    ],
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserDetailResponse:
    user = service.update_user(
        user_id=user_id,
        payload=payload,
    )
    record_admin_action(service, current_user, "user.updated", user)
    return UserDetailResponse.model_validate(user)


@router.post(
    "/{user_id}/enable",
    response_model=UserDetailResponse,
    summary="Enable user",
)
def enable_user(
    user_id: str,
    current_user: Annotated[
        User,
        Depends(require_permission(Permission.USERS_ENABLE)),
    ],
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserDetailResponse:
    user = service.enable_user(user_id)
    record_admin_action(service, current_user, "user.enabled", user)
    return UserDetailResponse.model_validate(user)


@router.post(
    "/{user_id}/disable",
    response_model=UserDetailResponse,
    summary="Disable user",
)
def disable_user(
    user_id: str,
    current_user: Annotated[
        User,
        Depends(require_permission(Permission.USERS_DISABLE)),
    ],
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserDetailResponse:
    user = service.disable_user(
        user_id=user_id,
        acting_user_id=current_user.id,
    )
    record_admin_action(service, current_user, "user.disabled", user)
    return UserDetailResponse.model_validate(user)


@router.post(
    "/{user_id}/lock",
    response_model=UserDetailResponse,
    summary="Lock user",
)
def lock_user(
    user_id: str,
    current_user: Annotated[
        User,
        Depends(require_permission(Permission.USERS_LOCK)),
    ],
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserDetailResponse:
    user = service.lock_user(
        user_id=user_id,
        acting_user_id=current_user.id,
    )
    record_admin_action(service, current_user, "user.locked", user)
    return UserDetailResponse.model_validate(user)


@router.post(
    "/{user_id}/unlock",
    response_model=UserDetailResponse,
    summary="Unlock user",
)
def unlock_user(
    user_id: str,
    current_user: Annotated[
        User,
        Depends(require_permission(Permission.USERS_UNLOCK)),
    ],
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserDetailResponse:
    user = service.unlock_user(user_id)
    record_admin_action(service, current_user, "user.unlocked", user)
    return UserDetailResponse.model_validate(user)


@router.patch(
    "/{user_id}/role",
    response_model=UserDetailResponse,
    summary="Change user role",
)
def change_role(
    user_id: str,
    payload: ChangeRoleRequest,
    current_user: Annotated[
        User,
        Depends(require_permission(Permission.USERS_ROLE_CHANGE)),
    ],
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserDetailResponse:
    user = service.change_role(
        user_id=user_id,
        payload=payload,
    )
    record_admin_action(service, current_user, "user.role_changed", user)
    return UserDetailResponse.model_validate(user)


@router.post(
    "/{user_id}/reset-password",
    response_model=UserDetailResponse,
    summary="Reset user password",
)
def reset_password(
    user_id: str,
    payload: ResetPasswordRequest,
    current_user: Annotated[
        User,
        Depends(require_permission(Permission.USERS_PASSWORD_RESET)),
    ],
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserDetailResponse:
    user = service.reset_password(
        user_id=user_id,
        payload=payload,
    )
    record_admin_action(service, current_user, "user.password_reset", user)
    return UserDetailResponse.model_validate(user)


@router.patch(
    "/{user_id}/force-password-change",
    response_model=UserDetailResponse,
    summary="Set forced password-change state",
)
def force_password_change(
    user_id: str,
    payload: ForcePasswordChangeRequest,
    current_user: Annotated[
        User,
        Depends(require_permission(Permission.USERS_FORCE_PASSWORD_CHANGE)),
    ],
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserDetailResponse:
    user = service.set_force_password_change(
        user_id=user_id,
        payload=payload,
    )
    record_admin_action(service, current_user, "user.force_password_change_updated", user)
    return UserDetailResponse.model_validate(user)
