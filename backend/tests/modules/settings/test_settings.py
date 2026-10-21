from app.modules.audit_security_admin.administration.settings_manager import (
    get_effective_setting,
)
from app.modules.audit_security_admin.models import AdminSettingHistory
from app.modules.detection.models import DetectionSettings


def _token(client, email, password):
    response = client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def test_settings_overview_and_categories_are_actual_module_configuration(
    client, admin
):
    token = _token(client, admin.email, "AdminPassword123!")
    headers = {"Authorization": f"Bearer {token}"}

    overview = client.get("/api/v1/settings", headers=headers)
    assert overview.status_code == 200, overview.text
    assert {item["category"] for item in overview.json()["categories"]} == {
        "general",
        "detection",
        "risk",
        "models",
        "email_processing",
        "threat_intelligence",
        "notifications",
        "security",
    }

    email_settings = client.get("/api/v1/settings/email_processing", headers=headers)
    assert email_settings.status_code == 200
    limit = next(
        field
        for field in email_settings.json()["fields"]
        if field["key"] == "email.max_upload_mb"
    )
    assert limit["value"] == 20

    unsupported = client.get("/api/v1/settings/notifications", headers=headers)
    assert unsupported.status_code == 200
    assert unsupported.json()["supported"] is False
    assert unsupported.json()["fields"] == []


def test_settings_updates_use_existing_table_audit_and_effective_configuration(
    client, db, admin
):
    token = _token(client, admin.email, "AdminPassword123!")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.put(
        "/api/v1/settings/email_processing",
        headers=headers,
        json={
            "values": {"email.max_upload_mb": 32},
            "reason": "Increase approved upload size",
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()["changed_keys"] == ["email.max_upload_mb"]
    assert get_effective_setting(db, "email.max_upload_mb") == 32
    history = (
        db.query(AdminSettingHistory).filter_by(setting_key="email.max_upload_mb").one()
    )
    assert history.old_value == 20
    assert history.new_value == 32
    assert history.reason == "Increase approved upload size"


def test_invalid_threshold_update_is_atomic_and_rejected(client, db, admin):
    token = _token(client, admin.email, "AdminPassword123!")
    response = client.put(
        "/api/v1/settings/risk",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "values": {
                "detection.high_risk_threshold": 95,
                "detection.critical_risk_threshold": 90,
            },
            "reason": "Set risk thresholds",
        },
    )

    assert response.status_code == 422
    assert db.get(DetectionSettings, 1) is None


def test_detection_controls_write_to_canonical_detection_settings(client, db, admin):
    token = _token(client, admin.email, "AdminPassword123!")
    response = client.put(
        "/api/v1/settings/detection",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "values": {"enable_behavioral_analysis": False},
            "reason": "Pause behavioral processing",
        },
    )

    assert response.status_code == 200, response.text
    row = db.get(DetectionSettings, 1)
    assert row.enable_behavioral_analysis is False
    assert response.json()["changed_keys"] == ["enable_behavioral_analysis"]


def test_viewer_cannot_update_settings(client, viewer):
    token = _token(client, viewer.email, "ViewerPassword123!")
    response = client.put(
        "/api/v1/settings/general",
        headers={"Authorization": f"Bearer {token}"},
        json={"values": {"platform.display_name": "Changed"}, "reason": "Not allowed"},
    )
    assert response.status_code == 403
