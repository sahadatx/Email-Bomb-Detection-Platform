from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.modules.emails.collector import EmailCollector


RAW_EMAIL = """\
From: sender@example.com
To: analyst@example.com
Subject: Weekly Security Report
Message-ID: <message-001@example.com>
Date: Thu, 24 Sep 2026 10:30:00 +0000
Content-Type: text/plain; charset="utf-8"

This is a test security report.
"""


def test_collect_text_extracts_email_metadata() -> None:
    collector = EmailCollector()

    result = collector.collect_text(RAW_EMAIL)

    assert result.raw_content == RAW_EMAIL.replace("\r\n", "\n")
    assert result.message_id == "<message-001@example.com>"
    assert result.sender == "sender@example.com"
    assert result.recipients == "analyst@example.com"
    assert result.subject == "Weekly Security Report"
    assert result.received_at == datetime(
        2026,
        9,
        24,
        10,
        30,
        tzinfo=timezone.utc,
    )


def test_collect_text_generates_sha256_content_hash() -> None:
    import hashlib

    collector = EmailCollector()

    result = collector.collect_text(RAW_EMAIL)

    expected_hash = hashlib.sha256(
        RAW_EMAIL.encode("utf-8")
    ).hexdigest()

    assert result.content_hash == expected_hash
    assert len(result.content_hash) == 64


def test_collect_text_normalizes_line_endings() -> None:
    collector = EmailCollector()

    raw_email = RAW_EMAIL.replace("\n", "\r\n")

    result = collector.collect_text(raw_email)

    assert "\r\n" not in result.raw_content
    assert result.raw_content == RAW_EMAIL


def test_collect_text_rejects_empty_content() -> None:
    collector = EmailCollector()

    with pytest.raises(
        ValueError,
        match="Email content cannot be empty",
    ):
        collector.collect_text("")


def test_collect_bytes_collects_email() -> None:
    collector = EmailCollector()

    result = collector.collect_bytes(
        RAW_EMAIL.encode("utf-8")
    )

    assert result.message_id == "<message-001@example.com>"
    assert result.sender == "sender@example.com"
    assert result.subject == "Weekly Security Report"


def test_collect_bytes_rejects_empty_content() -> None:
    collector = EmailCollector()

    with pytest.raises(
        ValueError,
        match="Email content cannot be empty",
    ):
        collector.collect_bytes(b"")


def test_collect_text_handles_invalid_date() -> None:
    collector = EmailCollector()

    raw_email = RAW_EMAIL.replace(
        "Thu, 24 Sep 2026 10:30:00 +0000",
        "not-a-valid-date",
    )

    result = collector.collect_text(raw_email)

    assert result.received_at is None