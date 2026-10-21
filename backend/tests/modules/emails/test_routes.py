from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.modules.emails.collection_models import (
    CollectionJobStatus,
    CollectionSource,
)
from app.modules.users.models import User


RAW_EMAIL = """\
From: sender@example.com
To: analyst@example.com
Subject: API Security Notification
Message-ID: <api-test-001@example.com>
Date: Thu, 24 Sep 2026 12:00:00 +0000

API ingestion test email.
"""


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


def raw_payload(
    identifier: str = "api-test-001",
) -> dict[str, str]:
    return {
        "source": "raw_email",
        "source_identifier": identifier,
        "raw_content": RAW_EMAIL.replace(
            "api-test-001",
            identifier,
        ),
    }


# ============================================================
# RAW INGESTION
# ============================================================


def test_admin_can_ingest_email(
    client: TestClient,
    admin: User,
) -> None:
    token = login(
        client,
        admin.email,
        "AdminPassword123!",
    )

    response = client.post(
        "/api/v1/emails/ingest",
        headers=headers(token),
        json=raw_payload(),
    )

    assert response.status_code == 201, response.text

    body = response.json()

    assert body["source"] == "raw_email"
    assert body["source_identifier"] == "api-test-001"
    assert body["message_id"] == "<api-test-001@example.com>"
    assert body["sender"] == "sender@example.com"
    assert body["recipients"] == "analyst@example.com"
    assert body["subject"] == "API Security Notification"
    assert body["status"] == "ingested"
    assert len(body["content_hash"]) == 64
    assert "raw_content" not in body


def test_duplicate_email_returns_conflict(
    client: TestClient,
    admin: User,
) -> None:
    token = login(
        client,
        admin.email,
        "AdminPassword123!",
    )

    payload = raw_payload("duplicate-test-001")

    first_response = client.post(
        "/api/v1/emails/ingest",
        headers=headers(token),
        json=payload,
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/api/v1/emails/ingest",
        headers=headers(token),
        json=payload,
    )

    assert second_response.status_code == 409

    body = second_response.json()

    assert "already been ingested" in body["detail"]


def test_non_raw_source_is_rejected_by_ingest_endpoint(
    client: TestClient,
    admin: User,
) -> None:
    token = login(
        client,
        admin.email,
        "AdminPassword123!",
    )

    payload = raw_payload("invalid-source")
    payload["source"] = "imap"

    response = client.post(
        "/api/v1/emails/ingest",
        headers=headers(token),
        json=payload,
    )

    assert response.status_code == 422

    body = response.json()

    assert "only accepts source='raw_email'" in body["detail"]


def test_empty_email_content_is_rejected(
    client: TestClient,
    admin: User,
) -> None:
    token = login(
        client,
        admin.email,
        "AdminPassword123!",
    )

    payload = raw_payload("empty-content")
    payload["raw_content"] = ""

    response = client.post(
        "/api/v1/emails/ingest",
        headers=headers(token),
        json=payload,
    )

    assert response.status_code == 422


def test_invalid_email_source_is_rejected_by_schema(
    client: TestClient,
    admin: User,
) -> None:
    token = login(
        client,
        admin.email,
        "AdminPassword123!",
    )

    payload = raw_payload("invalid-enum")
    payload["source"] = "unknown"

    response = client.post(
        "/api/v1/emails/ingest",
        headers=headers(token),
        json=payload,
    )

    assert response.status_code == 422


# ============================================================
# EMAIL LIST / DETAIL
# ============================================================


def test_admin_can_list_emails(
    client: TestClient,
    admin: User,
) -> None:
    token = login(
        client,
        admin.email,
        "AdminPassword123!",
    )

    ingest_response = client.post(
        "/api/v1/emails/ingest",
        headers=headers(token),
        json=raw_payload("list-test-001"),
    )

    assert ingest_response.status_code == 201

    response = client.get(
        "/api/v1/emails",
        headers=headers(token),
    )

    assert response.status_code == 200, response.text

    body = response.json()

    assert body["total"] == 1
    assert body["page"] == 1
    assert body["page_size"] == 20
    assert len(body["items"]) == 1
    assert body["items"][0]["source"] == "raw_email"


def test_admin_can_get_email(
    client: TestClient,
    admin: User,
) -> None:
    token = login(
        client,
        admin.email,
        "AdminPassword123!",
    )

    response = client.post(
        "/api/v1/emails/ingest",
        headers=headers(token),
        json=raw_payload("get-test-001"),
    )

    assert response.status_code == 201

    email_id = response.json()["id"]

    detail_response = client.get(
        f"/api/v1/emails/{email_id}",
        headers=headers(token),
    )

    assert detail_response.status_code == 200

    body = detail_response.json()

    assert body["id"] == email_id
    assert body["subject"] == "API Security Notification"


def test_missing_email_returns_not_found(
    client: TestClient,
    admin: User,
) -> None:
    token = login(
        client,
        admin.email,
        "AdminPassword123!",
    )

    missing_id = str(uuid4())

    response = client.get(
        f"/api/v1/emails/{missing_id}",
        headers=headers(token),
    )

    assert response.status_code == 404

    body = response.json()

    assert "was not found" in body["detail"]


def test_invalid_email_uuid_returns_validation_error(
    client: TestClient,
    admin: User,
) -> None:
    token = login(
        client,
        admin.email,
        "AdminPassword123!",
    )

    response = client.get(
        "/api/v1/emails/not-a-uuid",
        headers=headers(token),
    )

    assert response.status_code == 422


# ============================================================
# PAGINATION VALIDATION
# ============================================================


def test_invalid_page_is_rejected(
    client: TestClient,
    admin: User,
) -> None:
    token = login(
        client,
        admin.email,
        "AdminPassword123!",
    )

    response = client.get(
        "/api/v1/emails",
        headers=headers(token),
        params={"page": 0},
    )

    assert response.status_code == 422


def test_invalid_page_size_is_rejected(
    client: TestClient,
    admin: User,
) -> None:
    token = login(
        client,
        admin.email,
        "AdminPassword123!",
    )

    response = client.get(
        "/api/v1/emails",
        headers=headers(token),
        params={"page_size": 101},
    )

    assert response.status_code == 422


def test_collection_jobs_invalid_page_is_rejected(
    client: TestClient,
    admin: User,
) -> None:
    token = login(
        client,
        admin.email,
        "AdminPassword123!",
    )

    response = client.get(
        "/api/v1/emails/collection-jobs",
        headers=headers(token),
        params={"page": 0},
    )

    assert response.status_code == 422


# ============================================================
# FILE UPLOAD
# ============================================================


def test_admin_can_upload_eml_file(
    client: TestClient,
    admin: User,
) -> None:
    token = login(
        client,
        admin.email,
        "AdminPassword123!",
    )

    response = client.post(
        "/api/v1/emails/upload",
        headers=headers(token),
        files={
            "file": (
                "security-alert.eml",
                RAW_EMAIL.encode(),
                "message/rfc822",
            ),
        },
    )

    assert response.status_code == 201, response.text

    body = response.json()

    assert body["source"] == "file_upload"
    assert body["source_identifier"] == "security-alert.eml"
    assert body["subject"] == "API Security Notification"


def test_upload_rejects_non_eml_file(
    client: TestClient,
    admin: User,
) -> None:
    token = login(
        client,
        admin.email,
        "AdminPassword123!",
    )

    response = client.post(
        "/api/v1/emails/upload",
        headers=headers(token),
        files={
            "file": (
                "email.txt",
                RAW_EMAIL.encode(),
                "text/plain",
            ),
        },
    )

    assert response.status_code == 422

    body = response.json()

    assert "Only .eml files are supported" in body["detail"]


def test_upload_rejects_empty_eml_file(
    client: TestClient,
    admin: User,
) -> None:
    token = login(
        client,
        admin.email,
        "AdminPassword123!",
    )

    response = client.post(
        "/api/v1/emails/upload",
        headers=headers(token),
        files={
            "file": (
                "empty.eml",
                b"",
                "message/rfc822",
            ),
        },
    )

    assert response.status_code == 422

    body = response.json()

    assert "empty" in body["detail"].lower()


def test_duplicate_uploaded_eml_returns_conflict(
    client: TestClient,
    admin: User,
) -> None:
    token = login(
        client,
        admin.email,
        "AdminPassword123!",
    )

    files = {
        "file": (
            "duplicate.eml",
            RAW_EMAIL.encode(),
            "message/rfc822",
        ),
    }

    first_response = client.post(
        "/api/v1/emails/upload",
        headers=headers(token),
        files=files,
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/api/v1/emails/upload",
        headers=headers(token),
        files=files,
    )

    assert second_response.status_code == 409


# ============================================================
# IMAP CONNECTION TEST
# ============================================================


def imap_payload() -> dict[str, object]:
    return {
        "server": "imap.example.com",
        "port": 993,
        "username": "analyst@example.com",
        "password": "TestPassword123!",
        "mailbox": "INBOX",
        "timeout": 30,
    }


def test_admin_can_test_imap_connection_successfully(
    client: TestClient,
    admin: User,
) -> None:
    token = login(
        client,
        admin.email,
        "AdminPassword123!",
    )

    with patch(
        "app.modules.emails.routes.EmailService.test_imap_connection",
        return_value=True,
    ):
        response = client.post(
            "/api/v1/emails/imap/test-connection",
            headers=headers(token),
            json=imap_payload(),
        )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert "successful" in body["message"].lower()


def test_imap_connection_failure_returns_success_false(
    client: TestClient,
    admin: User,
) -> None:
    token = login(
        client,
        admin.email,
        "AdminPassword123!",
    )

    with patch(
        "app.modules.emails.routes.EmailService.test_imap_connection",
        return_value=False,
    ):
        response = client.post(
            "/api/v1/emails/imap/test-connection",
            headers=headers(token),
            json=imap_payload(),
        )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is False


def test_imap_connection_exception_is_safely_handled(
    client: TestClient,
    admin: User,
) -> None:
    token = login(
        client,
        admin.email,
        "AdminPassword123!",
    )

    with patch(
        "app.modules.emails.routes.EmailService.test_imap_connection",
        side_effect=RuntimeError("internal connection error"),
    ):
        response = client.post(
            "/api/v1/emails/imap/test-connection",
            headers=headers(token),
            json=imap_payload(),
        )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is False
    assert "internal connection error" not in body["message"]


# ============================================================
# IMAP COLLECTION
# ============================================================


def collection_job_response(
    *,
    status: CollectionJobStatus = CollectionJobStatus.COMPLETED,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid4(),
        source=CollectionSource.IMAP,
        mailbox="INBOX",
        requested_count=10,
        fetched_count=10,
        ingested_count=8,
        duplicate_count=1,
        failed_count=1,
        status=status,
    )


def test_admin_can_collect_from_imap(
    client: TestClient,
    admin: User,
) -> None:
    token = login(
        client,
        admin.email,
        "AdminPassword123!",
    )

    job = collection_job_response()

    with patch(
        "app.modules.emails.routes.EmailService.collect_from_imap",
        return_value=job,
    ):
        response = client.post(
            "/api/v1/emails/imap/collect",
            headers=headers(token),
            json={
                **imap_payload(),
                "limit": 10,
                "retries": 2,
            },
        )

    assert response.status_code == 201

    body = response.json()

    assert body["job_id"] == str(job.id)
    assert body["source"] == "imap"
    assert body["mailbox"] == "INBOX"
    assert body["requested"] == 10
    assert body["fetched"] == 10
    assert body["ingested"] == 8
    assert body["duplicates"] == 1
    assert body["failed"] == 1
    assert body["status"] == "completed"


def test_imap_collection_error_returns_502(
    client: TestClient,
    admin: User,
) -> None:
    token = login(
        client,
        admin.email,
        "AdminPassword123!",
    )

    with patch(
        "app.modules.emails.routes.EmailService.collect_from_imap",
        side_effect=__import__(
            "app.modules.emails.service",
            fromlist=["EmailCollectionError"],
        ).EmailCollectionError(
            "IMAP email collection failed.",
        ),
    ):
        response = client.post(
            "/api/v1/emails/imap/collect",
            headers=headers(token),
            json={
                **imap_payload(),
                "limit": 10,
                "retries": 2,
            },
        )

    assert response.status_code == 502

    body = response.json()

    assert body["detail"] == "IMAP email collection failed."


def test_imap_collection_limit_validation(
    client: TestClient,
    admin: User,
) -> None:
    token = login(
        client,
        admin.email,
        "AdminPassword123!",
    )

    response = client.post(
        "/api/v1/emails/imap/collect",
        headers=headers(token),
        json={
            **imap_payload(),
            "limit": 0,
            "retries": 2,
        },
    )

    assert response.status_code == 422


# ============================================================
# COLLECTION JOBS
# ============================================================


def test_admin_can_list_collection_jobs(
    client: TestClient,
    admin: User,
) -> None:
    token = login(
        client,
        admin.email,
        "AdminPassword123!",
    )

    response = client.get(
        "/api/v1/emails/collection-jobs",
        headers=headers(token),
    )

    assert response.status_code == 200

    body = response.json()

    assert "items" in body
    assert "total" in body
    assert body["page"] == 1
    assert body["page_size"] == 20


def test_missing_collection_job_returns_not_found(
    client: TestClient,
    admin: User,
) -> None:
    token = login(
        client,
        admin.email,
        "AdminPassword123!",
    )

    response = client.get(
        f"/api/v1/emails/collection-jobs/{uuid4()}",
        headers=headers(token),
    )

    assert response.status_code == 404


def test_invalid_collection_job_uuid_returns_validation_error(
    client: TestClient,
    admin: User,
) -> None:
    token = login(
        client,
        admin.email,
        "AdminPassword123!",
    )

    response = client.get(
        "/api/v1/emails/collection-jobs/not-a-uuid",
        headers=headers(token),
    )

    assert response.status_code == 422


# ============================================================
# RBAC / AUTHENTICATION
# ============================================================


def test_viewer_cannot_ingest_email(
    client: TestClient,
    viewer: User,
) -> None:
    token = login(
        client,
        viewer.email,
        "ViewerPassword123!",
    )

    response = client.post(
        "/api/v1/emails/ingest",
        headers=headers(token),
        json=raw_payload("viewer-blocked"),
    )

    assert response.status_code == 403


def test_viewer_cannot_upload_email(
    client: TestClient,
    viewer: User,
) -> None:
    token = login(
        client,
        viewer.email,
        "ViewerPassword123!",
    )

    response = client.post(
        "/api/v1/emails/upload",
        headers=headers(token),
        files={
            "file": (
                "viewer.eml",
                RAW_EMAIL.encode(),
                "message/rfc822",
            ),
        },
    )

    assert response.status_code == 403


def test_viewer_cannot_test_imap_connection(
    client: TestClient,
    viewer: User,
) -> None:
    token = login(
        client,
        viewer.email,
        "ViewerPassword123!",
    )

    response = client.post(
        "/api/v1/emails/imap/test-connection",
        headers=headers(token),
        json=imap_payload(),
    )

    assert response.status_code == 403


def test_viewer_cannot_collect_imap_emails(
    client: TestClient,
    viewer: User,
) -> None:
    token = login(
        client,
        viewer.email,
        "ViewerPassword123!",
    )

    response = client.post(
        "/api/v1/emails/imap/collect",
        headers=headers(token),
        json={
            **imap_payload(),
            "limit": 10,
            "retries": 2,
        },
    )

    assert response.status_code == 403


def test_viewer_cannot_list_emails(
    client: TestClient,
    viewer: User,
) -> None:
    token = login(
        client,
        viewer.email,
        "ViewerPassword123!",
    )

    response = client.get(
        "/api/v1/emails",
        headers=headers(token),
    )

    assert response.status_code == 403


def test_viewer_cannot_get_email(
    client: TestClient,
    viewer: User,
) -> None:
    token = login(
        client,
        viewer.email,
        "ViewerPassword123!",
    )

    response = client.get(
        f"/api/v1/emails/{uuid4()}",
        headers=headers(token),
    )

    assert response.status_code == 403


def test_viewer_cannot_list_collection_jobs(
    client: TestClient,
    viewer: User,
) -> None:
    token = login(
        client,
        viewer.email,
        "ViewerPassword123!",
    )

    response = client.get(
        "/api/v1/emails/collection-jobs",
        headers=headers(token),
    )

    assert response.status_code == 403


def test_viewer_cannot_get_collection_job(
    client: TestClient,
    viewer: User,
) -> None:
    token = login(
        client,
        viewer.email,
        "ViewerPassword123!",
    )

    response = client.get(
        f"/api/v1/emails/collection-jobs/{uuid4()}",
        headers=headers(token),
    )

    assert response.status_code == 403


def test_unauthenticated_user_cannot_ingest_email(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/emails/ingest",
        json=raw_payload("unauthenticated"),
    )

    assert response.status_code == 401


def test_unauthenticated_user_cannot_list_emails(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/emails")

    assert response.status_code == 401


def test_unauthenticated_user_cannot_upload_email(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/emails/upload",
        files={
            "file": (
                "unauthenticated.eml",
                RAW_EMAIL.encode(),
                "message/rfc822",
            ),
        },
    )

    assert response.status_code == 401


def test_unauthenticated_user_cannot_collect_imap(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/emails/imap/collect",
        json={
            **imap_payload(),
            "limit": 10,
            "retries": 2,
        },
    )

    assert response.status_code == 401