from datetime import datetime, timedelta, timezone

from app.modules.users.models import UserSession


def _token(client, email, password):
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def test_users_summary_is_global_and_not_limited_to_page(client, admin):
    token = _token(client, admin.email, "AdminPassword123!")
    response = client.get("/api/v1/users/summary", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200, response.text
    assert response.json() == {"total": 1, "active": 1, "disabled": 0, "locked": 0}


def test_managed_sessions_never_return_token_jti_and_can_be_revoked(client, db, admin):
    token = _token(client, admin.email, "AdminPassword123!")
    session = UserSession(
        user_id=admin.id,
        token_jti="session-jti-secret",
        ip_address="192.0.2.12",
        user_agent="Firefox on Linux",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get(f"/api/v1/users/{admin.id}/sessions", headers=headers)
    assert response.status_code == 200, response.text
    assert len(response.json()) == 2  # login session plus managed test session
    managed = next(item for item in response.json() if item["id"] == session.id)
    assert "token_jti" not in managed
    assert managed["user_agent"] == "Firefox on Linux"

    revoked = client.delete(f"/api/v1/users/{admin.id}/sessions/{session.id}", headers=headers)
    assert revoked.status_code == 204, revoked.text
    db.refresh(session)
    assert session.revoked_at is not None
