from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .collection_models import (
    CollectionJob,
    CollectionJobStatus,
)


class CollectionJobRepository:
    """
    Repository for email collection job persistence.

    Responsibilities:
    - Create collection jobs.
    - Retrieve jobs.
    - Update job state/counters.
    - List jobs with pagination.

    Business logic belongs in EmailService.
    IMAP communication belongs in IMAPCollector.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, job: CollectionJob) -> CollectionJob:
        """Persist a new collection job."""

        self.db.add(job)
        self.db.flush()
        self.db.refresh(job)

        return job

    def get_by_id(self, job_id: UUID) -> CollectionJob | None:
        """Return a collection job by its UUID."""

        statement = select(CollectionJob).where(
            CollectionJob.id == job_id
        )

        return self.db.scalar(statement)

    def update(self, job: CollectionJob) -> CollectionJob:
        """Persist changes made to an existing collection job."""

        self.db.add(job)
        self.db.flush()
        self.db.refresh(job)

        return job

    def update_status(
        self,
        job: CollectionJob,
        status: CollectionJobStatus,
    ) -> CollectionJob:
        """Update only the lifecycle status of a collection job."""

        job.status = status

        return self.update(job)

    def list(
        self,
        *,
        page: int = 1,
        page_size: int = 30,
    ) -> tuple[list[CollectionJob], int]:
        """
        Return collection jobs ordered from newest to oldest.

        Returns:
            A tuple containing:
            - paginated collection jobs
            - total number of collection jobs
        """

        offset = (page - 1) * page_size

        items_statement = (
            select(CollectionJob)
            .order_by(CollectionJob.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )

        count_statement = select(
            func.count()
        ).select_from(CollectionJob)

        items = list(
            self.db.scalars(items_statement).all()
        )

        total = self.db.scalar(count_statement) or 0

        return items, total