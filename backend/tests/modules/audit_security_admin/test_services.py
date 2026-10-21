import pytest
from fastapi.testclient import TestClient
from uuid import UUID
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.core.database import get_db
from app.core.security import hash_password
from app.modules.audit_security_admin.models import AdminSetting, AdminSettingHistory, AuditEvent, MonitoringRule, SecurityAlert, SecurityEvent
from app.modules.detection.models import DetectionSettings
from app.modules.users.models import User, UserRole, UserSession
from app.modules.emails.collection_models import CollectionJob
from app.modules.audit_security_admin.audit.service import AuditService, record_audit
from app.modules.audit_security_admin.errors import AdminDomainError
from app.modules.audit_security_admin.security_monitoring.service import SecurityMonitoringService
from app.modules.audit_security_admin.administration.settings_manager import list_settings, update_setting
from app.main import app


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    tables = [User.__table__, UserSession.__table__, CollectionJob.__table__, AuditEvent.__table__, MonitoringRule.__table__, SecurityAlert.__table__, SecurityEvent.__table__, AdminSetting.__table__, AdminSettingHistory.__table__, DetectionSettings.__table__]
    Base.metadata.create_all(engine, tables=tables)
    session = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine, tables=tables)
        engine.dispose()


@pytest.fixture
def admin(db):
    actor = User(email="admin@example.com", username="admin", full_name="System Administrator", password_hash=hash_password("AdminPassword123!"), role=UserRole.ADMIN, is_active=True, is_locked=False, force_password_change=False, failed_login_attempts=0)
    db.add(actor)
    db.commit()
    return actor


def test_audit_summary_search_and_sensitive_value_redaction(db, admin):
    record_audit(
        db,
        actor=admin,
        action="user.password_reset",
        target_type="user",
        target_id=admin.id,
        target_label=admin.username,
        details={"credential": {"api_key": "do-not-return", "changed": True}},
    )
    record_audit(db, actor=admin, action="user.update_failed", status="failure")
    db.commit()

    service = AuditService(db)
    page = service.list(page=1, page_size=1, search="password_reset")
    detail = service.detail(UUID(page["items"][0]["id"]))
    summary = service.summary()

    assert page["total"] == 1
    assert summary == {"total_events": 2, "failed_actions": 1, "security_events": 0, "active_users": 1}
    assert detail["details"]["credential"]["api_key"] == "[REDACTED]"


def test_monitoring_rule_generates_alert_and_validates_state(db, admin):
    service = SecurityMonitoringService(db)
    rule = service.save_rule(
        {
            "name": "Critical activity",
            "event_type": "login_failure",
            "severity": "critical",
            "condition": {"field": "severity", "operator": "equals", "value": "critical"},
            "enabled": True,
        },
        admin,
    )
    db.flush()

    result = service.ingest(
        {"event_type": "login_failure", "title": "Repeated login failures", "severity": "critical", "source": "Authentication"},
        actor=admin,
    )
    db.flush()

    assert result["event"]["related_alert_id"] == result["alerts"][0]["id"]
    assert service.summary()["critical_alerts"] == 1
    assert rule["name"] == "Critical activity"
    second = service.ingest({"event_type": "login_failure", "title": "Repeated login failures", "severity": "critical", "source": "Authentication"}, actor=admin)
    db.flush()
    assert second["alerts"][0]["id"] == result["alerts"][0]["id"]
    assert second["alerts"][0]["event_count"] == 2

    isolated = service.ingest({"event_type": "login_failure", "title": "Repeated login failures", "severity": "critical", "source": "Authentication", "source_ip": "203.0.113.8"}, actor=admin)
    db.flush()
    assert isolated["alerts"][0]["id"] != result["alerts"][0]["id"]

    updated = service.transition_alert(
        __import__("uuid").UUID(result["alerts"][0]["id"]),
        {"status": "resolved", "resolution_note": "Verified and contained."},
        admin,
    )
    assert updated["status"] == "resolved"

    try:
        service.save_rule({"name": "Unsafe", "event_type": "*", "severity": "high", "condition": {"field": "details", "operator": "contains", "value": "x"}}, admin)
    except AdminDomainError:
        pass
    else:
        raise AssertionError("Unsafe rule fields must be rejected")


def test_risk_threshold_settings_reflect_detection_configuration(db, admin):
    updated = update_setting(db, "detection.high_risk_threshold", 65, "Align threshold with review policy", admin)
    db.flush()

    settings = {item["key"]: item for item in list_settings(db)}
    assert updated["value"] == 65
    assert settings["detection.high_risk_threshold"]["value"] == 65
    try:
        update_setting(db, "detection.critical_risk_threshold", 60, "Invalid ordering", admin)
    except AdminDomainError:
        pass
    else:
        raise AssertionError("Critical threshold must stay above high threshold")


def test_authenticated_audit_api_and_login_audit_capture(db, admin):
    viewer = User(email="viewer@example.com", username="viewer", full_name="Read Only Viewer", password_hash=hash_password("ViewerPassword123!"), role=UserRole.VIEWER, is_active=True, is_locked=False, force_password_change=False, failed_login_attempts=0)
    db.add(viewer)
    db.commit()
    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as client:
            login = client.post("/api/v1/auth/login", json={"email": admin.email, "password": "AdminPassword123!"})
            assert login.status_code == 200
            token = login.json()["access_token"]
            response = client.get("/api/v1/audit", headers={"Authorization": f"Bearer {token}"})
            assert response.status_code == 200
            assert any(item["action"] == "auth.login_succeeded" for item in response.json()["items"])
            summary = client.get("/api/v1/audit/summary", headers={"Authorization": f"Bearer {token}"})
            assert summary.status_code == 200
            assert summary.json()["total_events"] >= 1
            security_event = client.post("/api/v1/security-monitoring/events", headers={"Authorization": f"Bearer {token}"}, json={"event_type": "test_signal", "title": "Credential telemetry", "severity": "high", "source": "Test", "actor_id": "attacker-controlled", "details": {"api_key": "secret"}})
            assert security_event.status_code == 201
            assert security_event.json()["event"]["actor_id"] == admin.id
            assert security_event.json()["event"]["details"]["api_key"] == "[REDACTED]"
            failed_login = client.post("/api/v1/auth/login", json={"email": admin.email, "password": "wrong-password"})
            assert failed_login.status_code == 401
            events = client.get("/api/v1/security-monitoring/events", headers={"Authorization": f"Bearer {token}"})
            assert events.status_code == 200
            assert any(event["event_type"] == "auth.login_failed" for event in events.json()["items"])
            assert client.get("/api/v1/administration/settings", headers={"Authorization": f"Bearer {token}"}).status_code == 200
            assert client.get("/api/v1/administration/health", headers={"Authorization": f"Bearer {token}"}).status_code == 200
            viewer_login = client.post("/api/v1/auth/login", json={"email": viewer.email, "password": "ViewerPassword123!"})
            viewer_token = viewer_login.json()["access_token"]
            assert client.get("/api/v1/security-monitoring/events", headers={"Authorization": f"Bearer {viewer_token}"}).status_code == 200
            assert client.get("/api/v1/administration/settings", headers={"Authorization": f"Bearer {viewer_token}"}).status_code == 403
            assert client.post("/api/v1/security-monitoring/events", headers={"Authorization": f"Bearer {viewer_token}"}, json={"event_type": "bad", "title": "Unauthorized", "severity": "high", "source": "test"}).status_code == 403
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_security_event_filters_and_job_pagination_are_consistent(db, admin):
    service = SecurityMonitoringService(db)
    service.ingest({"event_type": "auth.login_failed", "title": "Failed sign in", "severity": "high", "source": "Authentication", "actor_id": admin.id, "source_ip": "198.51.100.10"}, actor=admin)
    service.ingest({"event_type": "email_detection.risk", "title": "High risk detection", "severity": "high", "source": "Detection", "source_ip": "203.0.113.10"}, actor=admin)
    db.add_all([
        CollectionJob(source="raw_email", mailbox="first", status="completed", requested_count=10, fetched_count=10),
        CollectionJob(source="raw_email", mailbox="second", status="failed", requested_count=10, fetched_count=3),
    ])
    db.flush()
    result = service.list_events(page=1, page_size=10, actor_id=admin.id, source_ip="198.51", severity="high")
    assert result["total"] == 1
    assert result["items"][0]["actor_name"] == admin.full_name

    from app.modules.audit_security_admin.administration.job_manager import list_jobs
    jobs = list_jobs(db, page=1, page_size=1)
    assert jobs["total"] == 2
    assert len(jobs["items"]) == 1
    assert jobs["summary"]["failed_jobs"] == 1
    filtered = list_jobs(db, page=1, page_size=10, status="failed", search="second")
    assert filtered["total"] == 1
    assert filtered["items"][0]["status"] == "failed"
