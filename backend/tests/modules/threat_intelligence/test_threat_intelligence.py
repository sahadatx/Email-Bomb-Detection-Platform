from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.modules.emails.models import (
    Email,
    EmailGroundTruthLabel,
    EmailSource,
    EmailStatus,
)
from app.modules.emails.repository import EmailRepository
from app.modules.emails.schemas import EmailIngestRequest
from app.modules.emails.service import EmailService
from app.modules.threat_intelligence.models import ThreatIndicator, ThreatMatch
from app.modules.threat_intelligence.schemas import FeedCreate
from app.modules.threat_intelligence.service import (
    ThreatService,
    _extract_records,
    _fetch_feed_records,
)
from app.modules.threat_intelligence.validators import (
    normalize_indicator,
    validate_public_feed_url,
)


@pytest.mark.parametrize(
    ("kind", "value", "expected"),
    [
        ("domain", "Example.COM.", "example.com"),
        ("ip", "192.0.2.10", "192.0.2.10"),
        ("email", "Abuse@Example.com", "abuse@example.com"),
        ("hash", "A" * 64, "a" * 64),
    ],
)
def test_indicator_values_are_normalized(kind, value, expected):
    assert normalize_indicator(value, kind) == expected


def test_indicator_rejects_invalid_type_value():
    with pytest.raises(ValueError):
        normalize_indicator("not a host/path", "domain")


def test_external_feed_url_rejects_plain_http_and_private_ip():
    with pytest.raises(ValueError):
        validate_public_feed_url("http://example.org/iocs.csv")
    with pytest.raises(ValueError):
        validate_public_feed_url("https://127.0.0.1/iocs.json")


def test_internal_feed_rejects_external_credentials():
    with pytest.raises(
        ValueError, match="Internal feeds do not use external authentication"
    ):
        FeedCreate(
            name="Internal IOC Feed",
            feed_type="internal",
            auth_type="bearer",
            credential="secret-token",
        )


def test_viewer_can_read_but_cannot_manage_indicators(client, viewer):
    login = client.post(
        "/api/v1/auth/login",
        json={"email": viewer.email, "password": "ViewerPassword123!"},
    )
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    assert (
        client.get(
            "/api/v1/threat-intelligence/indicators", headers=headers
        ).status_code
        == 200
    )
    response = client.post(
        "/api/v1/threat-intelligence/indicators",
        headers=headers,
        json={"value": "restricted.example", "indicator_type": "domain"},
    )
    assert response.status_code == 403


def test_stix_bundle_and_json_feed_records_are_normalized():
    records = _extract_records(
        "stix_taxii",
        b'{"type":"bundle","objects":[{"type":"indicator","pattern":"[domain-name:value = \'malware.example\']","severity":"high"}]}',
    )
    assert records[0]["normalized_value"] == "malware.example"
    assert records[0]["indicator_type"] == "domain"
    assert records[0]["severity"] == "high"


def test_taxii_collection_follows_bounded_next_tokens(monkeypatch):
    from contextlib import nullcontext
    from types import SimpleNamespace
    from urllib.parse import urlencode

    from app.modules.threat_intelligence import service

    pages = [
        b'{"objects":[{"type":"indicator","pattern":"[domain-name:value = \'one.example\']"}],"more":true,"next":"cursor-2"}',
        b'{"objects":[{"type":"indicator","pattern":"[domain-name:value = \'two.example\']"}],"more":false}',
    ]

    class Client:
        def __init__(self):
            self.requests = []

        def stream(self, method, url, *, params=None, **kwargs):
            self.requests.append((method, url, params, kwargs))
            query = f"?{urlencode(params)}" if params else ""
            response = SimpleNamespace(
                request=SimpleNamespace(url=f"{url}{query}"),
                raise_for_status=lambda: None,
                iter_bytes=lambda: iter([pages[len(self.requests) - 1]]),
            )
            return nullcontext(response)

    monkeypatch.setattr(service, "validate_public_feed_url", lambda url: url)
    monkeypatch.setattr(service, "_safe_feed_host", lambda url: None)
    client = Client()
    feed = SimpleNamespace(
        url="https://feed.example/taxii2/collections/collection-id/objects/",
        feed_type="stix_taxii",
    )

    records = _fetch_feed_records(client, feed, {}, None)

    assert [record["normalized_value"] for record in records] == [
        "one.example",
        "two.example",
    ]
    assert len(client.requests) == 2
    assert client.requests[1][2] == {"next": "cursor-2"}


def test_new_email_is_matched_against_active_indicator(db):
    indicator = ThreatIndicator(
        value="malware.example",
        normalized_value="malware.example",
        indicator_type="domain",
        severity="high",
        source="manual",
        status="active",
    )
    email = Email(
        source=EmailSource.RAW_EMAIL,
        ground_truth_label=EmailGroundTruthLabel.NORMAL,
        sender="alerts@malware.example",
        raw_content="From: alerts@malware.example\nSubject: Notice\n\nHello",
        content_hash=uuid4().hex,
        status=EmailStatus.INGESTED,
    )
    db.add_all([indicator, email])
    db.flush()

    created = ThreatService(db).reconcile_email(email)
    match = (
        db.query(ThreatMatch)
        .filter_by(email_id=email.id, indicator_id=indicator.id)
        .one()
    )

    assert created == 1
    assert match.matched_field == "sender"
    assert match.match_status == "new"
    assert ThreatService(db).reconcile_email(email) == 0
    start = datetime.now(timezone.utc) - timedelta(days=1)
    end = datetime.now(timezone.utc) + timedelta(days=1)
    listed = ThreatService(db).list_matches(
        page=1, page_size=20, search=str(email.id), start=start, end=end
    )
    overview = ThreatService(db).overview(start=start, end=end)
    summary = ThreatService(db).match_summary(start=start, end=end)
    assert listed["total"] == 1
    assert overview["threat_matches"] == 1
    assert overview["critical_threats"] == 0
    assert overview["total_indicators"] == 1
    assert overview["trends"][-1]["indicators"] == 1
    assert summary["matched_emails"] == 1


def test_email_ingestion_integrates_with_threat_matching(db):
    db.add(
        ThreatIndicator(
            value="phishing.example",
            normalized_value="phishing.example",
            indicator_type="domain",
            severity="critical",
            source="manual",
            status="active",
        )
    )
    db.flush()
    service = EmailService(EmailRepository(db))
    ingested = service.ingest(
        EmailIngestRequest(
            ground_truth_label=EmailGroundTruthLabel.NORMAL,
            raw_content="From: notice@phishing.example\nTo: analyst@example.org\nSubject: Security notice\n\nPlease review.",
        )
    )
    match = db.query(ThreatMatch).filter_by(email_id=ingested.id).one()
    assert match.matched_field == "sender"
    assert match.detection_id is None
