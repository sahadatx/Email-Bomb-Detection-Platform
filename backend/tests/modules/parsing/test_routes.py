from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient


def test_parsing_health(
    client: TestClient,
):
    response = client.get(
        "/api/v1/parsing/health"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["module"] == "parsing"
    assert data["status"] == "ready"


def test_parsing_list_requires_authentication(
    client: TestClient,
):
    response = client.get(
        "/api/v1/parsing/emails"
    )

    assert response.status_code in {
        401,
        403,
    }


def test_parsing_get_requires_authentication(
    client: TestClient,
):
    response = client.get(
        f"/api/v1/parsing/emails/{uuid4()}"
    )

    assert response.status_code in {
        401,
        403,
    }


def test_parsing_single_parse_requires_authentication(
    client: TestClient,
):
    response = client.post(
        f"/api/v1/parsing/emails/{uuid4()}/parse"
    )

    assert response.status_code in {
        401,
        403,
    }


def test_parsing_batch_requires_authentication(
    client: TestClient,
):
    response = client.post(
        "/api/v1/parsing/emails/parse",
        json={
            "email_ids": [
                str(uuid4()),
            ]
        },
    )

    assert response.status_code in {
        401,
        403,
    }