from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.permissions import Permission
from app.core.rbac import (
    ROLE_PERMISSIONS,
    get_role_permissions,
    has_all_permissions,
    has_any_permission,
    has_permission,
)
from app.modules.users.models import User, UserRole


# ============================================================================
# Test Helpers
# ============================================================================


def login(
    client: TestClient,
    email: str,
    password: str,
) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200, response.text

    body = response.json()

    assert "access_token" in body
    assert body["token_type"] == "bearer"

    return body["access_token"]


def headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
    }


# ============================================================================
# Policy Tests
# ============================================================================


def test_all_roles_have_rbac_policy() -> None:
    for role in UserRole:
        assert role in ROLE_PERMISSIONS


def test_expected_roles_are_defined() -> None:
    assert set(UserRole) == {
        UserRole.ADMIN,
        UserRole.SECURITY_ANALYST,
        UserRole.EMAIL_ANALYST,
        UserRole.VIEWER,
    }


def test_admin_has_all_permissions() -> None:
    permissions = get_role_permissions(UserRole.ADMIN)

    assert permissions == frozenset(Permission)


@pytest.mark.parametrize(
    "role",
    [
        UserRole.SECURITY_ANALYST,
        UserRole.EMAIL_ANALYST,
        UserRole.VIEWER,
    ],
)
def test_non_admin_roles_do_not_have_user_management_permissions(
    role: UserRole,
) -> None:
    permissions = get_role_permissions(role)

    assert Permission.USERS_READ not in permissions
    assert Permission.USERS_CREATE not in permissions
    assert Permission.USERS_UPDATE not in permissions
    assert Permission.USERS_ENABLE not in permissions
    assert Permission.USERS_DISABLE not in permissions
    assert Permission.USERS_LOCK not in permissions
    assert Permission.USERS_UNLOCK not in permissions
    assert Permission.USERS_ROLE_CHANGE not in permissions
    assert Permission.USERS_PASSWORD_RESET not in permissions
    assert Permission.USERS_FORCE_PASSWORD_CHANGE not in permissions


@pytest.mark.parametrize(
    "role",
    list(UserRole),
)
def test_all_roles_have_profile_permissions(
    role: UserRole,
) -> None:
    permissions = get_role_permissions(role)

    assert Permission.PROFILE_READ in permissions
    assert Permission.PROFILE_PASSWORD_CHANGE in permissions
    assert Permission.PROFILE_SESSIONS_READ in permissions
    assert Permission.PROFILE_SESSION_REVOKE in permissions


@pytest.mark.parametrize(
    "role",
    list(UserRole),
)
def test_all_roles_have_system_health_permission(
    role: UserRole,
) -> None:
    permissions = get_role_permissions(role)

    assert Permission.SYSTEM_HEALTH_READ in permissions


# ============================================================================
# Permission Helper Tests
# ============================================================================


class UserStub:
    def __init__(self, role: UserRole) -> None:
        self.role = role


def test_has_permission_returns_true_when_granted() -> None:
    user = UserStub(UserRole.ADMIN)

    assert has_permission(
        user,
        Permission.USERS_CREATE,
    )


def test_has_permission_returns_false_when_missing() -> None:
    user = UserStub(UserRole.VIEWER)

    assert not has_permission(
        user,
        Permission.USERS_CREATE,
    )


def test_has_all_permissions_returns_true_when_all_granted() -> None:
    user = UserStub(UserRole.ADMIN)

    assert has_all_permissions(
        user,
        {
            Permission.USERS_READ,
            Permission.USERS_CREATE,
            Permission.USERS_UPDATE,
        },
    )


def test_has_all_permissions_returns_false_when_one_missing() -> None:
    user = UserStub(UserRole.VIEWER)

    assert not has_all_permissions(
        user,
        {
            Permission.PROFILE_READ,
            Permission.USERS_CREATE,
        },
    )


def test_has_any_permission_returns_true_when_one_granted() -> None:
    user = UserStub(UserRole.VIEWER)

    assert has_any_permission(
        user,
        {
            Permission.PROFILE_READ,
            Permission.USERS_CREATE,
        },
    )


def test_has_any_permission_returns_false_when_none_granted() -> None:
    user = UserStub(UserRole.VIEWER)

    assert not has_any_permission(
        user,
        {
            Permission.USERS_CREATE,
            Permission.USERS_UPDATE,
            Permission.USERS_ROLE_CHANGE,
        },
    )


def test_permission_values_are_unique() -> None:
    values = [permission.value for permission in Permission]

    assert len(values) == len(set(values))


def test_permission_values_are_non_empty() -> None:
    for permission in Permission:
        assert permission.value.strip()


def test_permission_values_use_expected_format() -> None:
    for permission in Permission:
        parts = permission.value.split(":")

        assert len(parts) >= 2
        assert all(part.strip() for part in parts)


def test_role_permission_sets_are_immutable() -> None:
    for role, permissions in ROLE_PERMISSIONS.items():
        assert isinstance(role, UserRole)
        assert isinstance(permissions, frozenset)


# ============================================================================
# Authentication + RBAC Integration
# ============================================================================


def test_unauthenticated_user_cannot_list_users(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/users")

    assert response.status_code == 401


def test_viewer_cannot_list_users(
    client: TestClient,
    viewer: User,
) -> None:
    token = login(
        client,
        viewer.email,
        "ViewerPassword123!",
    )

    response = client.get(
        "/api/v1/users",
        headers=headers(token),
    )

    assert response.status_code == 403

    body = response.json()

    assert body["success"] is False
    assert body["error"]["code"] == "authorization_error"


def test_security_analyst_cannot_list_users(
    client: TestClient,
    db: Session,
    viewer: User,
) -> None:
    viewer.role = UserRole.SECURITY_ANALYST

    db.commit()
    db.refresh(viewer)

    token = login(
        client,
        viewer.email,
        "ViewerPassword123!",
    )

    response = client.get(
        "/api/v1/users",
        headers=headers(token),
    )

    assert response.status_code == 403


def test_email_analyst_cannot_list_users(
    client: TestClient,
    db: Session,
    viewer: User,
) -> None:
    viewer.role = UserRole.EMAIL_ANALYST

    db.commit()
    db.refresh(viewer)

    token = login(
        client,
        viewer.email,
        "ViewerPassword123!",
    )

    response = client.get(
        "/api/v1/users",
        headers=headers(token),
    )

    assert response.status_code == 403


def test_admin_can_list_users(
    client: TestClient,
    admin: User,
) -> None:
    token = login(
        client,
        admin.email,
        "AdminPassword123!",
    )

    response = client.get(
        "/api/v1/users",
        headers=headers(token),
    )

    assert response.status_code == 200

    body = response.json()

    assert "items" in body
    assert "page" in body
    assert "page_size" in body
    assert "total" in body
    assert "pages" in body


# ============================================================================
# User Management Authorization
# ============================================================================


def test_viewer_cannot_create_user(
    client: TestClient,
    viewer: User,
) -> None:
    token = login(
        client,
        viewer.email,
        "ViewerPassword123!",
    )

    response = client.post(
        "/api/v1/users",
        headers=headers(token),
        json={
            "email": "rbac-created@example.com",
            "username": "rbac_created_user",
            "full_name": "RBAC Created User",
            "password": "RbacCreatedPassword123!",
            "role": "VIEWER",
        },
    )

    assert response.status_code == 403


def test_viewer_cannot_read_user_details(
    client: TestClient,
    viewer: User,
    admin: User,
) -> None:
    token = login(
        client,
        viewer.email,
        "ViewerPassword123!",
    )

    response = client.get(
        f"/api/v1/users/{admin.id}",
        headers=headers(token),
    )

    assert response.status_code == 403


def test_viewer_cannot_update_user(
    client: TestClient,
    viewer: User,
    admin: User,
) -> None:
    token = login(
        client,
        viewer.email,
        "ViewerPassword123!",
    )

    response = client.patch(
        f"/api/v1/users/{admin.id}",
        headers=headers(token),
        json={
            "full_name": "Unauthorized Update",
        },
    )

    assert response.status_code == 403


def test_viewer_cannot_enable_user(
    client: TestClient,
    viewer: User,
    admin: User,
) -> None:
    token = login(
        client,
        viewer.email,
        "ViewerPassword123!",
    )

    response = client.post(
        f"/api/v1/users/{admin.id}/enable",
        headers=headers(token),
    )

    assert response.status_code == 403


def test_viewer_cannot_disable_user(
    client: TestClient,
    viewer: User,
    admin: User,
) -> None:
    token = login(
        client,
        viewer.email,
        "ViewerPassword123!",
    )

    response = client.post(
        f"/api/v1/users/{admin.id}/disable",
        headers=headers(token),
    )

    assert response.status_code == 403


def test_viewer_cannot_lock_user(
    client: TestClient,
    viewer: User,
    admin: User,
) -> None:
    token = login(
        client,
        viewer.email,
        "ViewerPassword123!",
    )

    response = client.post(
        f"/api/v1/users/{admin.id}/lock",
        headers=headers(token),
    )

    assert response.status_code == 403


def test_viewer_cannot_unlock_user(
    client: TestClient,
    viewer: User,
    admin: User,
) -> None:
    token = login(
        client,
        viewer.email,
        "ViewerPassword123!",
    )

    response = client.post(
        f"/api/v1/users/{admin.id}/unlock",
        headers=headers(token),
    )

    assert response.status_code == 403


def test_viewer_cannot_change_user_role(
    client: TestClient,
    viewer: User,
    admin: User,
) -> None:
    token = login(
        client,
        viewer.email,
        "ViewerPassword123!",
    )

    response = client.patch(
        f"/api/v1/users/{admin.id}/role",
        headers=headers(token),
        json={
            "role": "VIEWER",
        },
    )

    assert response.status_code == 403


def test_viewer_cannot_reset_user_password(
    client: TestClient,
    viewer: User,
    admin: User,
) -> None:
    token = login(
        client,
        viewer.email,
        "ViewerPassword123!",
    )

    response = client.post(
        f"/api/v1/users/{admin.id}/reset-password",
        headers=headers(token),
        json={
            "new_password": "NewAdminPassword123!",
        },
    )

    assert response.status_code == 403


def test_viewer_cannot_force_password_change(
    client: TestClient,
    viewer: User,
    admin: User,
) -> None:
    token = login(
        client,
        viewer.email,
        "ViewerPassword123!",
    )

    response = client.patch(
        f"/api/v1/users/{admin.id}/force-password-change",
        headers=headers(token),
        json={
            "force_password_change": True,
        },
    )

    assert response.status_code == 403


# ============================================================================
# ADMIN Authorization
# ============================================================================


def test_admin_can_read_user_details(
    client: TestClient,
    admin: User,
    viewer: User,
) -> None:
    token = login(
        client,
        admin.email,
        "AdminPassword123!",
    )

    response = client.get(
        f"/api/v1/users/{viewer.id}",
        headers=headers(token),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == viewer.id


def test_admin_can_create_user(
    client: TestClient,
    admin: User,
) -> None:
    token = login(
        client,
        admin.email,
        "AdminPassword123!",
    )

    response = client.post(
        "/api/v1/users",
        headers=headers(token),
        json={
            "email": "rbac-created@example.com",
            "username": "rbac_created_user",
            "full_name": "RBAC Created User",
            "password": "RbacCreatedPassword123!",
            "role": "VIEWER",
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["email"] == "rbac-created@example.com"
    assert body["username"] == "rbac_created_user"
    assert body["role"] == "VIEWER"


# ============================================================================
# Self-Service Authorization
# ============================================================================


def test_viewer_can_read_own_profile(
    client: TestClient,
    viewer: User,
) -> None:
    token = login(
        client,
        viewer.email,
        "ViewerPassword123!",
    )

    response = client.get(
        "/api/v1/users/me",
        headers=headers(token),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == viewer.id
    assert body["email"] == viewer.email


# ============================================================================
# Authentication / RBAC Regression
# ============================================================================


def test_admin_role_is_preserved_after_authentication(
    client: TestClient,
    admin: User,
) -> None:
    token = login(
        client,
        admin.email,
        "AdminPassword123!",
    )

    response = client.get(
        "/api/v1/auth/me",
        headers=headers(token),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == admin.id
    assert body["role"] == UserRole.ADMIN.value


def test_viewer_role_is_preserved_after_authentication(
    client: TestClient,
    viewer: User,
) -> None:
    token = login(
        client,
        viewer.email,
        "ViewerPassword123!",
    )

    response = client.get(
        "/api/v1/auth/me",
        headers=headers(token),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == viewer.id
    assert body["role"] == UserRole.VIEWER.value


def test_locked_admin_cannot_authenticate(
    client: TestClient,
    db: Session,
    admin: User,
) -> None:
    admin.is_locked = True

    db.commit()
    db.refresh(admin)

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": admin.email,
            "password": "AdminPassword123!",
        },
    )

    assert response.status_code == 401


def test_disabled_admin_cannot_authenticate(
    client: TestClient,
    db: Session,
    admin: User,
) -> None:
    admin.is_active = False

    db.commit()
    db.refresh(admin)

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": admin.email,
            "password": "AdminPassword123!",
        },
    )

    assert response.status_code == 401