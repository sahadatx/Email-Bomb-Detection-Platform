from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modules.users.models import User


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
# User Listing
# ============================================================================


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

    assert body["total"] == 1
    assert body["items"][0]["email"] == admin.email


# ============================================================================
# Create User
# ============================================================================


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
            "email": "analyst@example.com",
            "username": "analyst",
            "full_name": "Security Analyst",
            "password": "AnalystPassword123!",
            "role": "SECURITY_ANALYST",
            "is_active": True,
            "force_password_change": False,
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["email"] == "analyst@example.com"
    assert body["username"] == "analyst"
    assert body["full_name"] == "Security Analyst"
    assert body["role"] == "SECURITY_ANALYST"
    assert body["is_active"] is True
    assert body["is_locked"] is False


def test_duplicate_email_is_rejected(
    client: TestClient,
    admin: User,
) -> None:
    token = login(
        client,
        admin.email,
        "AdminPassword123!",
    )

    payload = {
        "email": "duplicate@example.com",
        "username": "firstuser",
        "full_name": "First User",
        "password": "StrongPassword123!",
        "role": "VIEWER",
    }

    first_response = client.post(
        "/api/v1/users",
        headers=headers(token),
        json=payload,
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/api/v1/users",
        headers=headers(token),
        json={
            **payload,
            "username": "seconduser",
        },
    )

    assert second_response.status_code == 409


def test_duplicate_username_is_rejected(
    client: TestClient,
    admin: User,
) -> None:
    token = login(
        client,
        admin.email,
        "AdminPassword123!",
    )

    first_response = client.post(
        "/api/v1/users",
        headers=headers(token),
        json={
            "email": "first@example.com",
            "username": "sameusername",
            "full_name": "First User",
            "password": "StrongPassword123!",
            "role": "VIEWER",
        },
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/api/v1/users",
        headers=headers(token),
        json={
            "email": "second@example.com",
            "username": "sameusername",
            "full_name": "Second User",
            "password": "StrongPassword123!",
            "role": "VIEWER",
        },
    )

    assert second_response.status_code == 409


# ============================================================================
# User Details
# ============================================================================


def test_admin_can_get_user_details(
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
    assert body["email"] == viewer.email
    assert body["username"] == viewer.username
    assert body["role"] == "VIEWER"


# ============================================================================
# Update User
# ============================================================================


def test_admin_can_update_user(
    client: TestClient,
    admin: User,
    viewer: User,
) -> None:
    token = login(
        client,
        admin.email,
        "AdminPassword123!",
    )

    response = client.patch(
        f"/api/v1/users/{viewer.id}",
        headers=headers(token),
        json={
            "full_name": "Updated Viewer",
            "username": "updatedviewer",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["full_name"] == "Updated Viewer"
    assert body["username"] == "updatedviewer"


# ============================================================================
# Enable / Disable
# ============================================================================


def test_admin_can_disable_user(
    client: TestClient,
    admin: User,
    viewer: User,
) -> None:
    token = login(
        client,
        admin.email,
        "AdminPassword123!",
    )

    response = client.post(
        f"/api/v1/users/{viewer.id}/disable",
        headers=headers(token),
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_admin_can_enable_user(
    client: TestClient,
    db: Session,
    admin: User,
    viewer: User,
) -> None:
    viewer.is_active = False

    db.commit()
    db.refresh(viewer)

    assert viewer.is_active is False

    token = login(
        client,
        admin.email,
        "AdminPassword123!",
    )

    response = client.post(
        f"/api/v1/users/{viewer.id}/enable",
        headers=headers(token),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["is_active"] is True


def test_admin_cannot_disable_themselves(
    client: TestClient,
    admin: User,
) -> None:
    token = login(
        client,
        admin.email,
        "AdminPassword123!",
    )

    response = client.post(
        f"/api/v1/users/{admin.id}/disable",
        headers=headers(token),
    )

    assert response.status_code == 422


# ============================================================================
# Lock / Unlock
# ============================================================================


def test_admin_can_lock_user(
    client: TestClient,
    admin: User,
    viewer: User,
) -> None:
    token = login(
        client,
        admin.email,
        "AdminPassword123!",
    )

    response = client.post(
        f"/api/v1/users/{viewer.id}/lock",
        headers=headers(token),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["is_locked"] is True
    assert body["locked_at"] is not None


def test_admin_can_unlock_user(
    client: TestClient,
    db: Session,
    admin: User,
    viewer: User,
) -> None:
    viewer.is_locked = True
    viewer.locked_at = datetime.now(timezone.utc)
    viewer.failed_login_attempts = 5

    db.commit()
    db.refresh(viewer)

    assert viewer.is_locked is True
    assert viewer.failed_login_attempts == 5

    token = login(
        client,
        admin.email,
        "AdminPassword123!",
    )

    response = client.post(
        f"/api/v1/users/{viewer.id}/unlock",
        headers=headers(token),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == viewer.id
    assert body["is_locked"] is False
    assert body["locked_at"] is None
    assert body["failed_login_attempts"] == 0


def test_admin_cannot_lock_themselves(
    client: TestClient,
    admin: User,
) -> None:
    token = login(
        client,
        admin.email,
        "AdminPassword123!",
    )

    response = client.post(
        f"/api/v1/users/{admin.id}/lock",
        headers=headers(token),
    )

    assert response.status_code == 422


# ============================================================================
# Role Management
# ============================================================================


def test_admin_can_change_role(
    client: TestClient,
    admin: User,
    viewer: User,
) -> None:
    token = login(
        client,
        admin.email,
        "AdminPassword123!",
    )

    response = client.patch(
        f"/api/v1/users/{viewer.id}/role",
        headers=headers(token),
        json={
            "role": "EMAIL_ANALYST",
        },
    )

    assert response.status_code == 200
    assert response.json()["role"] == "EMAIL_ANALYST"


# ============================================================================
# Password Administration
# ============================================================================


def test_admin_can_reset_password(
    client: TestClient,
    admin: User,
    viewer: User,
) -> None:
    token = login(
        client,
        admin.email,
        "AdminPassword123!",
    )

    response = client.post(
        f"/api/v1/users/{viewer.id}/reset-password",
        headers=headers(token),
        json={
            "new_password": "NewViewerPassword123!",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["force_password_change"] is True


def test_admin_can_force_password_change(
    client: TestClient,
    admin: User,
    viewer: User,
) -> None:
    token = login(
        client,
        admin.email,
        "AdminPassword123!",
    )

    response = client.patch(
        f"/api/v1/users/{viewer.id}/force-password-change",
        headers=headers(token),
        json={
            "force_password_change": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["force_password_change"] is True


# ============================================================================
# Self-Service
# ============================================================================


def test_user_can_view_own_profile(
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
    assert body["username"] == viewer.username


def test_user_can_change_own_password(
    client: TestClient,
    viewer: User,
) -> None:
    token = login(
        client,
        viewer.email,
        "ViewerPassword123!",
    )

    response = client.post(
        "/api/v1/users/me/password",
        headers=headers(token),
        json={
            "current_password": "ViewerPassword123!",
            "new_password": "NewViewerPassword123!",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["force_password_change"] is False

    logout_response = client.post(
        "/api/v1/auth/logout",
        headers=headers(token),
    )

    assert logout_response.status_code == 204

    new_token = login(
        client,
        viewer.email,
        "NewViewerPassword123!",
    )

    assert new_token


def test_wrong_current_password_is_rejected(
    client: TestClient,
    viewer: User,
) -> None:
    token = login(
        client,
        viewer.email,
        "ViewerPassword123!",
    )

    response = client.post(
        "/api/v1/users/me/password",
        headers=headers(token),
        json={
            "current_password": "WrongPassword123!",
            "new_password": "NewViewerPassword123!",
        },
    )

    assert response.status_code == 422


# ============================================================================
# Administrative Authorization
# ============================================================================


def test_non_admin_cannot_list_users(
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


def test_non_admin_cannot_create_user(
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
            "email": "blocked@example.com",
            "username": "blockeduser",
            "full_name": "Blocked User",
            "password": "BlockedPassword123!",
            "role": "VIEWER",
        },
    )

    assert response.status_code == 403


# ============================================================================
# Search and Filtering
# ============================================================================


def test_user_search(
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
        "/api/v1/users",
        headers=headers(token),
        params={
            "search": "Viewer",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 1
    assert body["items"][0]["id"] == viewer.id


def test_user_role_filter(
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
        "/api/v1/users",
        headers=headers(token),
        params={
            "role": "VIEWER",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 1
    assert body["items"][0]["role"] == "VIEWER"


def test_user_active_filter(
    client: TestClient,
    db: Session,
    admin: User,
    viewer: User,
) -> None:
    viewer.is_active = False

    db.commit()
    db.refresh(viewer)

    token = login(
        client,
        admin.email,
        "AdminPassword123!",
    )

    response = client.get(
        "/api/v1/users",
        headers=headers(token),
        params={
            "is_active": False,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 1
    assert body["items"][0]["id"] == viewer.id
    assert body["items"][0]["is_active"] is False


def test_user_locked_filter(
    client: TestClient,
    db: Session,
    admin: User,
    viewer: User,
) -> None:
    viewer.is_locked = True
    viewer.locked_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(viewer)

    token = login(
        client,
        admin.email,
        "AdminPassword123!",
    )

    response = client.get(
        "/api/v1/users",
        headers=headers(token),
        params={
            "is_locked": True,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 1
    assert body["items"][0]["id"] == viewer.id
    assert body["items"][0]["is_locked"] is True


# ============================================================================
# Missing User
# ============================================================================


def test_get_missing_user_returns_404(
    client: TestClient,
    admin: User,
) -> None:
    token = login(
        client,
        admin.email,
        "AdminPassword123!",
    )

    response = client.get(
        "/api/v1/users/does-not-exist",
        headers=headers(token),
    )

    assert response.status_code == 404

    body = response.json()

    assert body["success"] is False
    assert body["error"]["code"] == "resource_not_found"