from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.modules.emails.models import (
    Email,
    EmailSource,
    EmailStatus,
)
from app.modules.parsing.schemas import ParsingStatus
from app.modules.parsing.service import (
    ParsingEmailNotFoundError,
    ParsingService,
)


class FakeEmailRepository:
    """
    Lightweight repository double for service tests.

    These tests intentionally avoid the database because the
    service layer should be testable independently.
    """

    def __init__(
        self,
        emails: list[Email] | None = None,
    ) -> None:
        self.emails = emails or []

    def get_by_id(
        self,
        email_id,
    ) -> Email | None:
        for email in self.emails:
            if email.id == email_id:
                return email

        return None

    def list(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Email], int]:

        offset = (page - 1) * page_size

        items = self.emails[
            offset : offset + page_size
        ]

        return items, len(self.emails)


class FakeParser:
    """
    Parser double used to isolate ParsingService tests.
    """

    def __init__(
        self,
        parsed_email,
    ) -> None:
        self.parsed_email = parsed_email

    def parse(
        self,
        raw_content,
    ):
        return self.parsed_email


def build_email(
    *,
    recipients: str | None = (
        "bob@example.com, carol@example.com"
    ),
) -> Email:
    """
    Build a test email whose stored Module 02 metadata and
    raw MIME content represent the same message.

    The raw MIME content is the source consumed by Module 03.
    """

    recipient_header = (
        recipients
        if recipients is not None
        else ""
    )

    raw_content = (
        "From: alice@example.com\r\n"
        f"To: {recipient_header}\r\n"
        "Message-ID: <test@example.com>\r\n"
        "Subject: Parsing Test Email\r\n"
        "\r\n"
        "Hello."
    )

    return Email(
        id=uuid4(),
        source=EmailSource.RAW_EMAIL,
        source_identifier="test-source",
        message_id="<test@example.com>",
        sender="alice@example.com",
        recipients=recipients,
        subject="Parsing Test Email",
        raw_content=raw_content,
        content_hash="a" * 64,
        received_at=datetime.now(timezone.utc),
        collected_at=datetime.now(timezone.utc),
        status=EmailStatus.INGESTED,
    )

def test_get_email_returns_module_02_email():
    email = build_email()

    repository = FakeEmailRepository(
        [email]
    )

    service = ParsingService(
        email_repository=repository
    )

    result = service.get_email(
        email.id
    )

    assert result is email


def test_get_email_raises_when_email_does_not_exist():
    email_id = uuid4()

    repository = FakeEmailRepository()

    service = ParsingService(
        email_repository=repository
    )

    with pytest.raises(
        ParsingEmailNotFoundError
    ):
        service.get_email(email_id)


def test_list_emails_returns_workspace_items():
    first = build_email()
    second = build_email()

    repository = FakeEmailRepository(
        [first, second]
    )

    service = ParsingService(
        email_repository=repository
    )

    items, total = service.list_emails(
        page=1,
        page_size=20,
    )

    assert total == 2
    assert len(items) == 2

    assert items[0].email_id == first.id
    assert items[0].subject == first.subject
    assert (
        items[0].parsing_status
        == ParsingStatus.PENDING
    )


def test_parse_email_returns_parsing_response():
    email = build_email()

    repository = FakeEmailRepository(
        [email]
    )

    service = ParsingService(
        email_repository=repository
    )

    result = service.parse_email(
        email.id
    )

    assert result.email_id == email.id
    assert result.source == EmailSource.RAW_EMAIL
    assert result.status == EmailStatus.INGESTED

    assert (
        result.identity.message_id
        == "<test@example.com>"
    )

    assert (
        result.identity.subject
        == "Parsing Test Email"
    )

    assert (
        result.identity.sender
        == "alice@example.com"
    )

    assert result.identity.recipients == [
        "bob@example.com",
        "carol@example.com",
    ]

    assert result.parsing.parser_version == "1.0.0"

    assert result.parsing.status in {
        ParsingStatus.PARSED,
        ParsingStatus.WARNING,
        ParsingStatus.FAILED,
    }


def test_parse_email_does_not_expose_raw_content():
    email = build_email()

    repository = FakeEmailRepository(
        [email]
    )

    service = ParsingService(
        email_repository=repository
    )

    result = service.parse_email(
        email.id
    )

    assert not hasattr(
        result,
        "raw_content",
    )


def test_parse_emails_supports_batch():
    first = build_email()
    second = build_email()

    repository = FakeEmailRepository(
        [first, second]
    )

    service = ParsingService(
        email_repository=repository
    )

    results = service.parse_emails(
        [
            first.id,
            second.id,
        ]
    )

    assert len(results) == 2
    assert results[0].email_id == first.id
    assert results[1].email_id == second.id


def test_missing_recipients_return_empty_list():
    email = build_email(
        recipients=None
    )

    repository = FakeEmailRepository(
        [email]
    )

    service = ParsingService(
        email_repository=repository
    )

    result = service.parse_email(
        email.id
    )

    assert result.identity.recipients == []


def test_list_emails_is_paginated():
    emails = [
        build_email(),
        build_email(),
        build_email(),
    ]

    repository = FakeEmailRepository(
        emails
    )

    service = ParsingService(
        email_repository=repository
    )

    items, total = service.list_emails(
        page=2,
        page_size=2,
    )

    assert total == 3
    assert len(items) == 1
    assert (
        items[0].email_id
        == emails[2].id
    )