from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base, get_db
from app.core.security import hash_password
from app.main import app
from app.modules.users.models import User, UserRole


TEST_DATABASE_URL = "sqlite:///./test_authentication.db"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


@pytest.fixture()
def db() -> Session:
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db: Session):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture()
def user(db: Session) -> User:
    test_user = User(
        email="admin@example.com",
        username="admin",
        full_name="Test Administrator",
        password_hash=hash_password("StrongPassword123!"),
        role=UserRole.ADMIN,
        is_active=True,
        is_locked=False,
        force_password_change=False,
        failed_login_attempts=0,
    )

    db.add(test_user)
    db.commit()
    db.refresh(test_user)

    return test_user


def login(client: TestClient) -> dict:
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "admin@example.com",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 200
    return response.json()


def auth_headers(access_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
    }


# ---------------------------------------------------------------------------
# Successful authentication
# ---------------------------------------------------------------------------

def test_successful_login_creates_access_token_and_session(
    client: TestClient,
    db: Session,
    user: User,
) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": user.email,
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert body["expires_at"]

    db.refresh(user)

    assert user.failed_login_attempts == 0
    assert user.last_login_at is not None

    assert len(user.sessions) == 1
    assert user.sessions[0].revoked_at is None


# ---------------------------------------------------------------------------
# Invalid credentials
# ---------------------------------------------------------------------------

def test_login_rejects_wrong_password(
    client: TestClient,
    user: User,
) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": user.email,
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401
    assert response.json()["success"] is False
    assert response.json()["error"]["code"] == "authentication_error"


def test_login_rejects_unknown_email(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "unknown@example.com",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "authentication_error"


# ---------------------------------------------------------------------------
# Account state
# ---------------------------------------------------------------------------

def test_disabled_account_cannot_login(
    client: TestClient,
    db: Session,
    user: User,
) -> None:
    user.is_active = False
    db.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": user.email,
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Account is disabled."


def test_locked_account_cannot_login(
    client: TestClient,
    db: Session,
    user: User,
) -> None:
    user.is_locked = True
    user.locked_at = datetime.now(timezone.utc)
    db.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": user.email,
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Account is locked."


# ---------------------------------------------------------------------------
# Failed-login lockout
# ---------------------------------------------------------------------------

def test_failed_logins_lock_account_after_five_attempts(
    client: TestClient,
    db: Session,
    user: User,
) -> None:
    for attempt in range(5):
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": user.email,
                "password": "WrongPassword123!",
            },
        )

        assert response.status_code == 401

        db.refresh(user)

        assert user.failed_login_attempts == attempt + 1

    assert user.is_locked is True
    assert user.locked_at is not None


# ---------------------------------------------------------------------------
# Current user
# ---------------------------------------------------------------------------

def test_get_current_user(
    client: TestClient,
    user: User,
) -> None:
    token_response = login(client)

    response = client.get(
        "/api/v1/auth/me",
        headers=auth_headers(token_response["access_token"]),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == user.id
    assert body["email"] == user.email
    assert body["username"] == user.username
    assert body["full_name"] == user.full_name
    assert body["role"] == "ADMIN"
    assert body["is_active"] is True
    assert body["is_locked"] is False
    assert body["force_password_change"] is False


# ---------------------------------------------------------------------------
# Authentication credentials
# ---------------------------------------------------------------------------

def test_current_user_requires_bearer_token(
    client: TestClient,
    user: User,
) -> None:
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "authentication_error"


def test_invalid_access_token_is_rejected(
    client: TestClient,
    user: User,
) -> None:
    response = client.get(
        "/api/v1/auth/me",
        headers=auth_headers("invalid-token"),
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "authentication_error"


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------

def test_list_sessions(
    client: TestClient,
    user: User,
) -> None:
    token_response = login(client)

    response = client.get(
        "/api/v1/auth/sessions",
        headers=auth_headers(token_response["access_token"]),
    )

    assert response.status_code == 200

    sessions = response.json()

    assert len(sessions) == 1
    assert sessions[0]["token_jti"]
    assert sessions[0]["revoked_at"] is None


def test_logout_revokes_current_session(
    client: TestClient,
    user: User,
) -> None:
    token_response = login(client)

    access_token = token_response["access_token"]

    response = client.post(
        "/api/v1/auth/logout",
        headers=auth_headers(access_token),
    )

    assert response.status_code == 204

    response = client.get(
        "/api/v1/auth/me",
        headers=auth_headers(access_token),
    )

    assert response.status_code == 401


def test_revoked_session_cannot_access_protected_endpoint(
    client: TestClient,
    user: User,
) -> None:
    token_response = login(client)

    access_token = token_response["access_token"]

    logout_response = client.post(
        "/api/v1/auth/logout",
        headers=auth_headers(access_token),
    )

    assert logout_response.status_code == 204

    response = client.get(
        "/api/v1/auth/sessions",
        headers=auth_headers(access_token),
    )

    assert response.status_code == 401


def test_revoke_specific_session(
    client: TestClient,
    user: User,
) -> None:
    first_login = login(client)

    first_token = first_login["access_token"]

    sessions_response = client.get(
        "/api/v1/auth/sessions",
        headers=auth_headers(first_token),
    )

    assert sessions_response.status_code == 200

    sessions = sessions_response.json()

    assert len(sessions) == 1

    session_id = sessions[0]["id"]

    response = client.delete(
        f"/api/v1/auth/sessions/{session_id}",
        headers=auth_headers(first_token),
    )

    assert response.status_code == 204

    response = client.get(
        "/api/v1/auth/me",
        headers=auth_headers(first_token),
    )

    assert response.status_code == 401


# ---------------------------------------------------------------------------
# User/session isolation
# ---------------------------------------------------------------------------

def test_user_cannot_revoke_another_users_session(
    client: TestClient,
    db: Session,
    user: User,
) -> None:
    second_user = User(
        email="second@example.com",
        username="second",
        full_name="Second User",
        password_hash=hash_password("StrongPassword123!"),
        role=UserRole.VIEWER,
        is_active=True,
        is_locked=False,
        force_password_change=False,
        failed_login_attempts=0,
    )

    db.add(second_user)
    db.commit()
    db.refresh(second_user)

    first_login = login(client)

    second_login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": second_user.email,
            "password": "StrongPassword123!",
        },
    )

    assert second_login_response.status_code == 200

    second_token = second_login_response.json()["access_token"]

    second_sessions_response = client.get(
        "/api/v1/auth/sessions",
        headers=auth_headers(second_token),
    )

    assert second_sessions_response.status_code == 200

    second_session_id = second_sessions_response.json()[0]["id"]

    response = client.delete(
        f"/api/v1/auth/sessions/{second_session_id}",
        headers=auth_headers(first_login["access_token"]),
    )

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Session expiration
# ---------------------------------------------------------------------------

def test_expired_session_is_rejected(
    client: TestClient,
    db: Session,
    user: User,
) -> None:
    token_response = login(client)

    db.refresh(user)

    session = user.sessions[0]
    session.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db.commit()

    response = client.get(
        "/api/v1/auth/me",
        headers=auth_headers(token_response["access_token"]),
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "authentication_error"