from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.modules.emails.collection_models import (
    CollectionJob,
    CollectionJobStatus,
    CollectionSource,
)
from app.modules.emails.collector import CollectedEmail
from app.modules.emails.imap_collector import (
    IMAPCollectionResult,
    IMAPCollectorError,
    IMAPMessage,
)
from app.modules.emails.models import Email, EmailSource, EmailStatus
from app.modules.emails.schemas import EmailIngestRequest, IMAPCollectionRequest
from app.modules.emails.service import (
    EmailAlreadyExistsError,
    EmailCollectionError,
    EmailNotFoundError,
    EmailService,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def repository() -> MagicMock:
    return MagicMock()


@pytest.fixture
def collection_repository() -> MagicMock:
    return MagicMock()


@pytest.fixture
def service(
    repository: MagicMock,
    collection_repository: MagicMock,
) -> EmailService:
    return EmailService(
        repository=repository,
        collection_repository=collection_repository,
    )


@pytest.fixture
def imap_request() -> IMAPCollectionRequest:
    return IMAPCollectionRequest(
        server="imap.example.com",
        port=993,
        username="analyst@example.com",
        password="SecretPassword123!",
        mailbox="INBOX",
        limit=10,
        timeout=30,
        retries=2,
    )


@pytest.fixture
def raw_email() -> str:
    return (
        "From: sender@example.com\r\n"
        "To: analyst@example.com\r\n"
        "Subject: Test Email\r\n"
        "Message-ID: <test-001@example.com>\r\n"
        "Date: Wed, 24 Sep 2026 12:00:00 +0000\r\n"
        "\r\n"
        "This is a test email."
    )


@pytest.fixture
def collected_email() -> CollectedEmail:
    return CollectedEmail(
        raw_content=(
            "From: sender@example.com\r\n"
            "To: analyst@example.com\r\n"
            "Subject: Test Email\r\n"
            "Message-ID: <test-001@example.com>\r\n"
            "\r\n"
            "This is a test email."
        ),
        content_hash="a" * 64,
        message_id="<test-001@example.com>",
        sender="sender@example.com",
        recipients="analyst@example.com",
        subject="Test Email",
        received_at=datetime(
            2026,
            9,
            24,
            12,
            0,
            tzinfo=timezone.utc,
        ),
    )


def make_collection_job(
    *,
    requested_count: int = 10,
    status: CollectionJobStatus = CollectionJobStatus.PENDING,
    source: CollectionSource = CollectionSource.IMAP,
    mailbox: str = "INBOX",
) -> CollectionJob:
    """
    Build a fully initialized collection job for service tests.

    SQLAlchemy defaults are applied during flush, not necessarily when
    a model instance is constructed. Explicitly initializing counters
    prevents test behavior from depending on ORM flush semantics.
    """
    return CollectionJob(
        id=uuid4(),
        source=source,
        mailbox=mailbox,
        status=status,
        requested_count=requested_count,
        fetched_count=0,
        ingested_count=0,
        duplicate_count=0,
        failed_count=0,
        error_message=None,
        started_at=None,
        completed_at=None,
    )


def make_collected_email(
    *,
    content_hash: str,
    message_id: str | None = None,
    sender: str | None = None,
    recipients: str | None = None,
    subject: str | None = None,
    raw_content: str = "raw email",
    received_at: datetime | None = None,
) -> CollectedEmail:
    return CollectedEmail(
        raw_content=raw_content,
        content_hash=content_hash,
        message_id=message_id,
        sender=sender,
        recipients=recipients,
        subject=subject,
        received_at=received_at,
    )


# ============================================================================
# Raw Email Ingestion
# ============================================================================


def test_ingest_persists_raw_email(
    service: EmailService,
    repository: MagicMock,
    raw_email: str,
) -> None:
    repository.get_by_content_hash.return_value = None

    expected_email = Email(
        source=EmailSource.RAW_EMAIL,
        source_identifier="api:test-001",
        message_id="<test-001@example.com>",
        sender="sender@example.com",
        recipients="analyst@example.com",
        subject="Test Email",
        raw_content=raw_email.replace("\r\n", "\n"),
        content_hash="hash-placeholder",
        status=EmailStatus.INGESTED,
    )

    repository.create.return_value = expected_email

    request = EmailIngestRequest(
        source=EmailSource.RAW_EMAIL,
        source_identifier="api:test-001",
        raw_content=raw_email,
    )

    collected = make_collected_email(
        content_hash="hash-placeholder",
        message_id="<test-001@example.com>",
        sender="sender@example.com",
        recipients="analyst@example.com",
        subject="Test Email",
        raw_content=raw_email.replace("\r\n", "\n"),
    )

    with patch.object(
        service.collector,
        "collect_text",
        return_value=collected,
    ) as collect_mock:
        result = service.ingest(request)

    assert result is expected_email

    collect_mock.assert_called_once_with(raw_email)

    repository.get_by_content_hash.assert_called_once_with(
        "hash-placeholder",
    )

    repository.create.assert_called_once()

    created = repository.create.call_args.args[0]

    assert created.source == EmailSource.RAW_EMAIL
    assert created.source_identifier == "api:test-001"
    assert created.message_id == "<test-001@example.com>"
    assert created.sender == "sender@example.com"
    assert created.recipients == "analyst@example.com"
    assert created.subject == "Test Email"
    assert created.content_hash == "hash-placeholder"
    assert created.status == EmailStatus.INGESTED


def test_ingest_raises_duplicate_error(
    service: EmailService,
    repository: MagicMock,
    raw_email: str,
) -> None:
    repository.get_by_content_hash.return_value = MagicMock(
        spec=Email,
    )

    request = EmailIngestRequest(
        source=EmailSource.RAW_EMAIL,
        raw_content=raw_email,
    )

    with pytest.raises(
        EmailAlreadyExistsError,
        match="same content has already been ingested",
    ):
        service.ingest(request)

    repository.create.assert_not_called()


def test_ingest_rejects_empty_content(
    service: EmailService,
) -> None:
    request = EmailIngestRequest(
        source=EmailSource.RAW_EMAIL,
        raw_content=" ",
    )

    with pytest.raises(ValueError):
        service.ingest(request)


# ============================================================================
# File Ingestion
# ============================================================================


def test_ingest_file_uses_file_upload_source(
    service: EmailService,
    repository: MagicMock,
    collected_email: CollectedEmail,
) -> None:
    repository.get_by_content_hash.return_value = None

    expected_email = Email(
        source=EmailSource.FILE_UPLOAD,
        source_identifier="sample.eml",
        raw_content=collected_email.raw_content,
        content_hash=collected_email.content_hash,
        status=EmailStatus.INGESTED,
    )

    repository.create.return_value = expected_email

    with patch.object(
        service.collector,
        "collect_bytes",
        return_value=collected_email,
    ) as collect_mock:
        result = service.ingest_file(
            b"raw email bytes",
            source_identifier="sample.eml",
        )

    assert result is expected_email

    collect_mock.assert_called_once_with(
        b"raw email bytes",
    )

    repository.get_by_content_hash.assert_called_once_with(
        collected_email.content_hash,
    )

    created = repository.create.call_args.args[0]

    assert created.source == EmailSource.FILE_UPLOAD
    assert created.source_identifier == "sample.eml"


def test_ingest_file_raises_duplicate_error(
    service: EmailService,
    repository: MagicMock,
    collected_email: CollectedEmail,
) -> None:
    repository.get_by_content_hash.return_value = MagicMock(
        spec=Email,
    )

    with patch.object(
        service.collector,
        "collect_bytes",
        return_value=collected_email,
    ):
        with pytest.raises(EmailAlreadyExistsError):
            service.ingest_file(
                b"duplicate email",
                source_identifier="duplicate.eml",
            )

    repository.create.assert_not_called()


# ============================================================================
# IMAP Connection Test
# ============================================================================


def test_test_imap_connection_returns_true(
    service: EmailService,
    imap_request: IMAPCollectionRequest,
) -> None:
    collector = MagicMock()
    collector.test_connection.return_value = True

    with patch.object(
        service,
        "_create_imap_collector",
        return_value=collector,
    ) as factory_mock:
        result = service.test_imap_connection(imap_request)

    assert result is True

    factory_mock.assert_called_once_with(
        imap_request,
    )

    collector.test_connection.assert_called_once_with()


def test_test_imap_connection_returns_false(
    service: EmailService,
    imap_request: IMAPCollectionRequest,
) -> None:
    collector = MagicMock()
    collector.test_connection.return_value = False

    with patch.object(
        service,
        "_create_imap_collector",
        return_value=collector,
    ):
        result = service.test_imap_connection(imap_request)

    assert result is False


# ============================================================================
# IMAP Collector Factory
# ============================================================================


def test_create_imap_collector_builds_correct_configuration(
    imap_request: IMAPCollectionRequest,
) -> None:
    collector = EmailService._create_imap_collector(
        imap_request,
    )

    assert collector.config.server == "imap.example.com"
    assert collector.config.port == 993
    assert collector.config.username == "analyst@example.com"
    assert collector.config.password == "SecretPassword123!"
    assert collector.config.mailbox == "INBOX"
    assert collector.config.timeout == 30
    assert collector.config.retries == 2


# ============================================================================
# IMAP Collection — Successful
# ============================================================================


def test_collect_from_imap_ingests_messages_and_creates_job(
    service: EmailService,
    repository: MagicMock,
    collection_repository: MagicMock,
    imap_request: IMAPCollectionRequest,
) -> None:
    job = make_collection_job(
        requested_count=10,
    )

    collection_repository.create.return_value = job
    repository.get_by_content_hash.return_value = None

    result = IMAPCollectionResult(
        requested=2,
        fetched=2,
        messages=(
            IMAPMessage(
                message_id="101",
                raw_content=(
                    b"From: first@example.com\r\n"
                    b"Subject: First\r\n"
                    b"\r\n"
                    b"First message"
                ),
            ),
            IMAPMessage(
                message_id="102",
                raw_content=(
                    b"From: second@example.com\r\n"
                    b"Subject: Second\r\n"
                    b"\r\n"
                    b"Second message"
                ),
            ),
        ),
    )

    collected_messages = [
        make_collected_email(
            content_hash="1" * 64,
            message_id="101",
            sender="first@example.com",
            subject="First",
            raw_content="first",
        ),
        make_collected_email(
            content_hash="2" * 64,
            message_id="102",
            sender="second@example.com",
            subject="Second",
            raw_content="second",
        ),
    ]

    with patch.object(
        service,
        "_create_imap_collector",
    ) as factory_mock:
        collector = MagicMock()
        collector.collect.return_value = result
        factory_mock.return_value = collector

        with patch.object(
            service.collector,
            "collect_bytes",
            side_effect=collected_messages,
        ) as collect_mock:
            returned_job = service.collect_from_imap(
                imap_request,
            )

    assert returned_job is job

    assert job.source == CollectionSource.IMAP
    assert job.fetched_count == 2
    assert job.ingested_count == 2
    assert job.duplicate_count == 0
    assert job.failed_count == 0
    assert job.status == CollectionJobStatus.COMPLETED

    assert job.started_at is not None
    assert job.completed_at is not None

    assert collection_repository.create.call_count == 1
    assert collection_repository.update.call_count >= 2

    factory_mock.assert_called_once_with(
        imap_request,
    )

    collector.collect.assert_called_once_with(
        limit=10,
    )

    assert collect_mock.call_count == 2
    assert repository.create.call_count == 2

    created_emails = [
        call.args[0]
        for call in repository.create.call_args_list
    ]

    assert all(
        email.source == EmailSource.IMAP
        for email in created_emails
    )

    assert created_emails[0].source_identifier == (
        "imap:analyst@example.com:INBOX:101"
    )

    assert created_emails[1].source_identifier == (
        "imap:analyst@example.com:INBOX:102"
    )


# ============================================================================
# IMAP Collection — Duplicate Handling
# ============================================================================


def test_collect_from_imap_counts_duplicate_messages(
    service: EmailService,
    repository: MagicMock,
    collection_repository: MagicMock,
    imap_request: IMAPCollectionRequest,
) -> None:
    job = make_collection_job(
        requested_count=2,
    )

    collection_repository.create.return_value = job

    result = IMAPCollectionResult(
        requested=2,
        fetched=2,
        messages=(
            IMAPMessage(
                message_id="101",
                raw_content=b"Email 1",
            ),
            IMAPMessage(
                message_id="102",
                raw_content=b"Email 2",
            ),
        ),
    )

    repository.get_by_content_hash.return_value = MagicMock(
        spec=Email,
    )

    with patch.object(
        service,
        "_create_imap_collector",
    ) as factory_mock:
        collector = MagicMock()
        collector.collect.return_value = result
        factory_mock.return_value = collector

        with patch.object(
            service.collector,
            "collect_bytes",
            side_effect=[
                make_collected_email(
                    content_hash="1" * 64,
                    message_id="101",
                    raw_content="email 1",
                ),
                make_collected_email(
                    content_hash="2" * 64,
                    message_id="102",
                    raw_content="email 2",
                ),
            ],
        ):
            returned_job = service.collect_from_imap(
                imap_request,
            )

    assert returned_job is job
    assert returned_job.fetched_count == 2
    assert returned_job.ingested_count == 0
    assert returned_job.duplicate_count == 2
    assert returned_job.failed_count == 0
    assert returned_job.status == CollectionJobStatus.FAILED

    repository.create.assert_not_called()


# ============================================================================
# IMAP Collection — Individual Message Failure
# ============================================================================


def test_collect_from_imap_counts_individual_message_failure(
    service: EmailService,
    repository: MagicMock,
    collection_repository: MagicMock,
    imap_request: IMAPCollectionRequest,
) -> None:
    job = make_collection_job(
        requested_count=2,
    )

    collection_repository.create.return_value = job
    repository.get_by_content_hash.return_value = None

    result = IMAPCollectionResult(
        requested=2,
        fetched=2,
        messages=(
            IMAPMessage(
                message_id="101",
                raw_content=b"valid email",
            ),
            IMAPMessage(
                message_id="102",
                raw_content=b"invalid email",
            ),
        ),
    )

    with patch.object(
        service,
        "_create_imap_collector",
    ) as factory_mock:
        collector = MagicMock()
        collector.collect.return_value = result
        factory_mock.return_value = collector

        with patch.object(
            service.collector,
            "collect_bytes",
            side_effect=[
                make_collected_email(
                    content_hash="1" * 64,
                    message_id="101",
                    subject="Valid",
                    raw_content="valid",
                ),
                ValueError("Unable to parse email"),
            ],
        ):
            returned_job = service.collect_from_imap(
                imap_request,
            )

    assert returned_job is job
    assert returned_job.fetched_count == 2
    assert returned_job.ingested_count == 1
    assert returned_job.failed_count == 1
    assert returned_job.duplicate_count == 0
    assert returned_job.status == CollectionJobStatus.PARTIAL

    assert repository.create.call_count == 1


# ============================================================================
# IMAP Collection — Collector Failure
# ============================================================================


def test_collect_from_imap_marks_job_failed_when_collector_fails(
    service: EmailService,
    collection_repository: MagicMock,
    imap_request: IMAPCollectionRequest,
) -> None:
    job = make_collection_job(
        requested_count=10,
    )

    collection_repository.create.return_value = job

    collector_error = IMAPCollectorError(
        "Unable to connect to IMAP server",
    )

    with patch.object(
        service,
        "_create_imap_collector",
    ) as factory_mock:
        collector = MagicMock()
        collector.collect.side_effect = collector_error
        factory_mock.return_value = collector

        with pytest.raises(
            EmailCollectionError,
            match="IMAP email collection failed",
        ):
            service.collect_from_imap(imap_request)

    assert job.status == CollectionJobStatus.FAILED
    assert job.error_message == str(collector_error)
    assert job.completed_at is not None

    assert collection_repository.create.call_count == 1
    assert collection_repository.update.call_count >= 2


def test_collect_from_imap_handles_unexpected_error(
    service: EmailService,
    collection_repository: MagicMock,
    imap_request: IMAPCollectionRequest,
) -> None:
    job = make_collection_job(
        requested_count=10,
    )

    collection_repository.create.return_value = job

    with patch.object(
        service,
        "_create_imap_collector",
    ) as factory_mock:
        collector = MagicMock()
        collector.collect.side_effect = RuntimeError(
            "unexpected failure",
        )
        factory_mock.return_value = collector

        with pytest.raises(
            EmailCollectionError,
            match="Unexpected error during IMAP email collection",
        ):
            service.collect_from_imap(imap_request)

    assert job.status == CollectionJobStatus.FAILED
    assert job.error_message == (
        "Unexpected error during email collection."
    )
    assert job.completed_at is not None

    assert collection_repository.create.call_count == 1
    assert collection_repository.update.call_count >= 2


# ============================================================================
# Collection Repository Configuration
# ============================================================================


def test_collect_from_imap_requires_collection_repository(
    repository: MagicMock,
    imap_request: IMAPCollectionRequest,
) -> None:
    service = EmailService(
        repository=repository,
        collection_repository=None,
    )

    with pytest.raises(
        EmailCollectionError,
        match="Collection job repository is not configured",
    ):
        service.collect_from_imap(imap_request)


def test_get_collection_job_requires_collection_repository(
    repository: MagicMock,
) -> None:
    service = EmailService(
        repository=repository,
        collection_repository=None,
    )

    with pytest.raises(
        EmailCollectionError,
        match="Collection job repository is not configured",
    ):
        service.get_collection_job(uuid4())


def test_list_collection_jobs_requires_collection_repository(
    repository: MagicMock,
) -> None:
    service = EmailService(
        repository=repository,
        collection_repository=None,
    )

    with pytest.raises(
        EmailCollectionError,
        match="Collection job repository is not configured",
    ):
        service.list_collection_jobs()


# ============================================================================
# Email Retrieval
# ============================================================================


def test_get_returns_existing_email(
    service: EmailService,
    repository: MagicMock,
) -> None:
    email_id = uuid4()

    email = MagicMock(spec=Email)
    email.id = email_id

    repository.get_by_id.return_value = email

    result = service.get(email_id)

    assert result is email

    repository.get_by_id.assert_called_once_with(
        email_id,
    )


def test_get_raises_when_email_does_not_exist(
    service: EmailService,
    repository: MagicMock,
) -> None:
    email_id = uuid4()

    repository.get_by_id.return_value = None

    with pytest.raises(
        EmailNotFoundError,
        match="was not found",
    ):
        service.get(email_id)


# ============================================================================
# Email Listing
# ============================================================================


def test_list_delegates_to_email_repository(
    service: EmailService,
    repository: MagicMock,
) -> None:
    emails = [
        MagicMock(spec=Email),
        MagicMock(spec=Email),
    ]

    repository.list.return_value = (
        emails,
        2,
    )

    result_items, result_total = service.list(
        page=2,
        page_size=10,
    )

    assert result_items == emails
    assert result_total == 2

    repository.list.assert_called_once_with(
        page=2,
        page_size=10,
    )


# ============================================================================
# Collection Job Retrieval
# ============================================================================


def test_get_collection_job_returns_existing_job(
    service: EmailService,
    collection_repository: MagicMock,
) -> None:
    job_id = uuid4()

    job = make_collection_job(
        requested_count=10,
        status=CollectionJobStatus.COMPLETED,
    )
    job.id = job_id

    collection_repository.get_by_id.return_value = job

    result = service.get_collection_job(job_id)

    assert result is job

    collection_repository.get_by_id.assert_called_once_with(
        job_id,
    )


def test_get_collection_job_raises_when_job_does_not_exist(
    service: EmailService,
    collection_repository: MagicMock,
) -> None:
    job_id = uuid4()

    collection_repository.get_by_id.return_value = None

    with pytest.raises(
        EmailNotFoundError,
        match="Collection job",
    ):
        service.get_collection_job(job_id)


def test_list_collection_jobs_delegates_to_repository(
    service: EmailService,
    collection_repository: MagicMock,
) -> None:
    jobs = [
        MagicMock(spec=CollectionJob),
        MagicMock(spec=CollectionJob),
    ]

    collection_repository.list.return_value = (
        jobs,
        2,
    )

    result_items, result_total = service.list_collection_jobs(
        page=1,
        page_size=20,
    )

    assert result_items == jobs
    assert result_total == 2

    collection_repository.list.assert_called_once_with(
        page=1,
        page_size=20,
    )


# ============================================================================
# Collection Status Resolution
# ============================================================================


@pytest.mark.parametrize(
    (
        "fetched",
        "ingested",
        "duplicates",
        "failed",
        "expected",
    ),
    [
        (
            0,
            0,
            0,
            0,
            CollectionJobStatus.COMPLETED,
        ),
        (
            5,
            5,
            0,
            0,
            CollectionJobStatus.COMPLETED,
        ),
        (
            5,
            4,
            1,
            0,
            CollectionJobStatus.PARTIAL,
        ),
        (
            5,
            4,
            0,
            1,
            CollectionJobStatus.PARTIAL,
        ),
        (
            5,
            0,
            0,
            5,
            CollectionJobStatus.FAILED,
        ),
        (
            5,
            0,
            5,
            0,
            CollectionJobStatus.FAILED,
        ),
    ],
)
def test_resolve_collection_status(
    fetched: int,
    ingested: int,
    duplicates: int,
    failed: int,
    expected: CollectionJobStatus,
) -> None:
    job = make_collection_job(
        requested_count=fetched,
        status=CollectionJobStatus.RUNNING,
    )

    job.fetched_count = fetched
    job.ingested_count = ingested
    job.duplicate_count = duplicates
    job.failed_count = failed

    result = EmailService._resolve_collection_status(job)

    assert result == expected


# ============================================================================
# IMAP Source and Lifecycle
# ============================================================================


def test_imap_collection_job_uses_imap_source(
    service: EmailService,
    collection_repository: MagicMock,
    imap_request: IMAPCollectionRequest,
) -> None:
    job = make_collection_job(
        requested_count=imap_request.limit,
    )

    collection_repository.create.return_value = job

    result = IMAPCollectionResult(
        requested=0,
        fetched=0,
        messages=(),
    )

    with patch.object(
        service,
        "_create_imap_collector",
    ) as factory_mock:
        collector = MagicMock()
        collector.collect.return_value = result
        factory_mock.return_value = collector

        returned_job = service.collect_from_imap(
            imap_request,
        )

    assert returned_job is job
    assert returned_job.source == CollectionSource.IMAP

    # The collection job is created with the correct initial configuration.
    created_job = collection_repository.create.call_args.args[0]

    assert created_job.source == CollectionSource.IMAP
    assert created_job.mailbox == "INBOX"
    assert created_job.requested_count == 10

    # The service must persist the job after changing its state.
    assert collection_repository.update.call_count >= 2

    # The final state for an empty successful collection is COMPLETED.
    assert returned_job.status == CollectionJobStatus.COMPLETED
    assert returned_job.completed_at is not None


# ============================================================================
# IMAP Message Metadata
# ============================================================================


def test_imap_collection_preserves_message_metadata(
    service: EmailService,
    repository: MagicMock,
    collection_repository: MagicMock,
    imap_request: IMAPCollectionRequest,
) -> None:
    job = make_collection_job(
        requested_count=1,
    )

    collection_repository.create.return_value = job
    repository.get_by_content_hash.return_value = None

    result = IMAPCollectionResult(
        requested=1,
        fetched=1,
        messages=(
            IMAPMessage(
                message_id="abc-123",
                raw_content=b"raw message",
            ),
        ),
    )

    received_at = datetime(
        2026,
        9,
        24,
        12,
        30,
        tzinfo=timezone.utc,
    )

    collected = make_collected_email(
        content_hash="f" * 64,
        message_id="<abc-123@example.com>",
        sender="sender@example.com",
        recipients="analyst@example.com",
        subject="Important message",
        raw_content="raw message",
        received_at=received_at,
    )

    with patch.object(
        service,
        "_create_imap_collector",
    ) as factory_mock:
        collector = MagicMock()
        collector.collect.return_value = result
        factory_mock.return_value = collector

        with patch.object(
            service.collector,
            "collect_bytes",
            return_value=collected,
        ):
            returned_job = service.collect_from_imap(
                imap_request,
            )

    assert returned_job.status == CollectionJobStatus.COMPLETED

    created_email = repository.create.call_args.args[0]

    # UUID generation belongs to SQLAlchemy flush/repository behavior,
    # not this mocked service test.
    assert created_email.source == EmailSource.IMAP
    assert created_email.source_identifier == (
        "imap:analyst@example.com:INBOX:abc-123"
    )
    assert created_email.message_id == (
        "<abc-123@example.com>"
    )
    assert created_email.sender == "sender@example.com"
    assert created_email.recipients == "analyst@example.com"
    assert created_email.subject == "Important message"
    assert created_email.raw_content == "raw message"
    assert created_email.content_hash == "f" * 64
    assert created_email.received_at == received_at
    assert created_email.status == EmailStatus.INGESTED