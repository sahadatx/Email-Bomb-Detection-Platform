from __future__ import annotations

from uuid import uuid4

from sqlalchemy.orm import Session

from app.modules.emails.collection_models import (
    CollectionJob,
    CollectionJobStatus,
    CollectionSource,
)
from app.modules.emails.collection_repository import CollectionJobRepository


def create_job(
    db: Session,
    *,
    source: CollectionSource = CollectionSource.IMAP,
    mailbox: str = "INBOX",
    status: CollectionJobStatus = CollectionJobStatus.PENDING,
    requested_count: int = 10,
    fetched_count: int = 0,
    ingested_count: int = 0,
    duplicate_count: int = 0,
    failed_count: int = 0,
) -> CollectionJob:
    repository = CollectionJobRepository(db)

    job = CollectionJob(
        id=uuid4(),
        source=source,
        mailbox=mailbox,
        status=status,
        requested_count=requested_count,
        fetched_count=fetched_count,
        ingested_count=ingested_count,
        duplicate_count=duplicate_count,
        failed_count=failed_count,
    )

    return repository.create(job)


def test_create_persists_collection_job(
    db: Session,
) -> None:
    repository = CollectionJobRepository(db)

    job = CollectionJob(
        source=CollectionSource.IMAP,
        mailbox="INBOX",
        status=CollectionJobStatus.PENDING,
        requested_count=25,
    )

    created = repository.create(job)

    assert created.id is not None
    assert created.source == CollectionSource.IMAP
    assert created.mailbox == "INBOX"
    assert created.status == CollectionJobStatus.PENDING
    assert created.requested_count == 25
    assert created.fetched_count == 0
    assert created.ingested_count == 0
    assert created.duplicate_count == 0
    assert created.failed_count == 0
    assert created.created_at is not None
    assert created.updated_at is not None


def test_get_by_id_returns_existing_job(
    db: Session,
) -> None:
    repository = CollectionJobRepository(db)

    created = create_job(
        db,
        requested_count=50,
    )

    found = repository.get_by_id(created.id)

    assert found is not None
    assert found.id == created.id
    assert found.source == CollectionSource.IMAP
    assert found.mailbox == "INBOX"
    assert found.requested_count == 50


def test_get_by_id_returns_none_for_unknown_job(
    db: Session,
) -> None:
    repository = CollectionJobRepository(db)

    result = repository.get_by_id(uuid4())

    assert result is None


def test_update_persists_collection_progress(
    db: Session,
) -> None:
    repository = CollectionJobRepository(db)

    job = create_job(
        db,
        requested_count=10,
    )

    job.status = CollectionJobStatus.RUNNING
    job.fetched_count = 10
    job.ingested_count = 7
    job.duplicate_count = 2
    job.failed_count = 1

    updated = repository.update(job)

    assert updated.status == CollectionJobStatus.RUNNING
    assert updated.fetched_count == 10
    assert updated.ingested_count == 7
    assert updated.duplicate_count == 2
    assert updated.failed_count == 1

    persisted = repository.get_by_id(job.id)

    assert persisted is not None
    assert persisted.status == CollectionJobStatus.RUNNING
    assert persisted.fetched_count == 10
    assert persisted.ingested_count == 7
    assert persisted.duplicate_count == 2
    assert persisted.failed_count == 1


def test_update_status_changes_job_status(
    db: Session,
) -> None:
    repository = CollectionJobRepository(db)

    job = create_job(
        db,
        status=CollectionJobStatus.PENDING,
    )

    updated = repository.update_status(
        job,
        CollectionJobStatus.RUNNING,
    )

    assert updated.status == CollectionJobStatus.RUNNING

    persisted = repository.get_by_id(job.id)

    assert persisted is not None
    assert persisted.status == CollectionJobStatus.RUNNING


def test_update_status_supports_completed_status(
    db: Session,
) -> None:
    repository = CollectionJobRepository(db)

    job = create_job(
        db,
        status=CollectionJobStatus.RUNNING,
    )

    updated = repository.update_status(
        job,
        CollectionJobStatus.COMPLETED,
    )

    assert updated.status == CollectionJobStatus.COMPLETED


def test_update_status_supports_partial_status(
    db: Session,
) -> None:
    repository = CollectionJobRepository(db)

    job = create_job(
        db,
        status=CollectionJobStatus.RUNNING,
    )

    updated = repository.update_status(
        job,
        CollectionJobStatus.PARTIAL,
    )

    assert updated.status == CollectionJobStatus.PARTIAL


def test_update_status_supports_failed_status(
    db: Session,
) -> None:
    repository = CollectionJobRepository(db)

    job = create_job(
        db,
        status=CollectionJobStatus.RUNNING,
    )

    updated = repository.update_status(
        job,
        CollectionJobStatus.FAILED,
    )

    assert updated.status == CollectionJobStatus.FAILED


def test_list_returns_jobs_and_total_count(
    db: Session,
) -> None:
    repository = CollectionJobRepository(db)

    create_job(db, requested_count=10)
    create_job(db, requested_count=20)
    create_job(db, requested_count=30)

    items, total = repository.list(
        page=1,
        page_size=20,
    )

    assert total == 3
    assert len(items) == 3


def test_list_respects_page_size(
    db: Session,
) -> None:
    repository = CollectionJobRepository(db)

    for count in range(1, 6):
        create_job(
            db,
            requested_count=count,
        )

    items, total = repository.list(
        page=1,
        page_size=2,
    )

    assert total == 5
    assert len(items) == 2


def test_list_supports_pagination(
    db: Session,
) -> None:
    repository = CollectionJobRepository(db)

    jobs = [
        create_job(
            db,
            requested_count=10,
        ),
        create_job(
            db,
            requested_count=20,
        ),
        create_job(
            db,
            requested_count=30,
        ),
        create_job(
            db,
            requested_count=40,
        ),
        create_job(
            db,
            requested_count=50,
        ),
    ]

    first_page, first_total = repository.list(
        page=1,
        page_size=2,
    )

    second_page, second_total = repository.list(
        page=2,
        page_size=2,
    )

    assert first_total == 5
    assert second_total == 5

    assert len(first_page) == 2
    assert len(second_page) == 2

    first_ids = {job.id for job in first_page}
    second_ids = {job.id for job in second_page}

    assert first_ids.isdisjoint(second_ids)

    all_test_ids = {job.id for job in jobs}

    assert first_ids.issubset(all_test_ids)
    assert second_ids.issubset(all_test_ids)


def test_list_returns_empty_result_when_no_jobs_exist(
    db: Session,
) -> None:
    repository = CollectionJobRepository(db)

    items, total = repository.list(
        page=1,
        page_size=20,
    )

    assert items == []
    assert total == 0


def test_list_orders_jobs_by_newest_first(
    db: Session,
) -> None:
    repository = CollectionJobRepository(db)

    older = create_job(
        db,
        requested_count=10,
    )

    newer = create_job(
        db,
        requested_count=20,
    )

    items, total = repository.list(
        page=1,
        page_size=20,
    )

    assert total == 2
    assert len(items) == 2

    assert items[0].id == newer.id
    assert items[1].id == older.id