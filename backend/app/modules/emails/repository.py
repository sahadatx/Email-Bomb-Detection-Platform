from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from .models import (
    Email,
    EmailGroundTruthLabel,
    EmailSource,
)


# ============================================================================
# CONSTANTS
# ============================================================================

DEFAULT_PAGE_SIZE = 30
MAX_PAGE_SIZE = 100


# ============================================================================
# EMAIL REPOSITORY
# ============================================================================


class EmailRepository:
    """
    Repository for canonical email records.

    This repository is responsible only for database access.

    Responsibilities:
        - Create email records.
        - Retrieve email records.
        - Detect duplicate content hashes.
        - Paginate email records.
        - Apply Email Management filters.
        - Calculate Email Management statistics.
        - Persist multiple email records in one transaction.
        - Delete records for compatibility with existing internal callers.

    Business rules and ingestion workflows belong to the service layer.
    """

    def __init__(
        self,
        db: Session,
    ) -> None:
        if db is None:
            raise ValueError(
                "Database session is required."
            )

        self.db = db

    # ========================================================================
    # CREATE
    # ========================================================================

    def create(
        self,
        email: Email,
    ) -> Email:
        """
        Add and flush one email record.

        The surrounding service owns transaction commit/rollback.
        """

        if email is None:
            raise ValueError(
                "Email record is required."
            )

        self.db.add(email)
        self.db.flush()
        self.db.refresh(email)

        return email

    def create_many(
        self,
        emails: list[Email],
    ) -> list[Email]:
        """
        Add and flush multiple email records.

        No commit is performed here.

        The service layer controls the transaction boundary.
        """

        if not emails:
            return []

        self.db.add_all(emails)
        self.db.flush()

        for email in emails:
            self.db.refresh(email)

        return emails

    # ========================================================================
    # READ — SINGLE EMAIL
    # ========================================================================

    def get_by_id(
        self,
        email_id: UUID,
    ) -> Email | None:
        """
        Return one email by UUID.
        """

        if email_id is None:
            return None

        statement = (
            select(Email)
            .where(
                Email.id == email_id,
            )
        )

        return self.db.scalar(
            statement,
        )

    def get_by_content_hash(
        self,
        content_hash: str,
    ) -> Email | None:
        """
        Return one email matching the supplied content hash.
        """

        if not content_hash:
            return None

        statement = (
            select(Email)
            .where(
                Email.content_hash == content_hash,
            )
            .limit(1)
        )

        return self.db.scalar(
            statement,
        )

    # ========================================================================
    # READ — MULTIPLE EMAILS
    # ========================================================================

    def get_by_ids(
        self,
        email_ids: list[UUID],
    ) -> list[Email]:
        """
        Return emails matching the supplied UUIDs.

        Results are ordered by newest creation time first.
        """

        if not email_ids:
            return []

        statement = (
            select(Email)
            .where(
                Email.id.in_(email_ids),
            )
            .order_by(
                Email.created_at.desc(),
                Email.id.desc(),
            )
        )

        return list(
            self.db.scalars(
                statement,
            ).all()
        )

    # ========================================================================
    # LIST / FILTER
    # ========================================================================

    def list(
        self,
        *,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
        search: str | None = None,
        source: EmailSource | None = None,
        ground_truth_label: (
            EmailGroundTruthLabel | None
        ) = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> tuple[list[Email], int]:
        """
        Return a filtered and paginated email collection.

        Supported filters:

            search
                Searches:
                    - subject
                    - sender
                    - recipients
                    - source identifier
                    - message ID

            source
                FILE_UPLOAD or RAW_EMAIL.

            ground_truth_label
                NORMAL or BOMBING.

            from_date
                Inclusive lower received_at boundary.

            to_date
                Inclusive upper received_at boundary.

        Returns:

            (items, total)
        """

        normalized_page = self._normalize_page(
            page,
        )

        normalized_page_size = (
            self._normalize_page_size(
                page_size,
            )
        )

        conditions = (
            self._build_filter_conditions(
                search=search,
                source=source,
                ground_truth_label=ground_truth_label,
                from_date=from_date,
                to_date=to_date,
            )
        )

        offset = (
            (normalized_page - 1)
            * normalized_page_size
        )

        items_statement = (
            select(Email)
            .where(*conditions)
            .order_by(
                Email.created_at.desc(),
                Email.id.desc(),
            )
            .offset(offset)
            .limit(
                normalized_page_size,
            )
        )

        count_statement = (
            select(
                func.count(Email.id),
            )
            .where(*conditions)
        )

        items = list(
            self.db.scalars(
                items_statement,
            ).all()
        )

        total = (
            self.db.scalar(
                count_statement,
            )
            or 0
        )

        return items, int(total)

    # ========================================================================
    # FILTER BUILDER
    # ========================================================================

    def _build_filter_conditions(
        self,
        *,
        search: str | None = None,
        source: EmailSource | None = None,
        ground_truth_label: (
            EmailGroundTruthLabel | None
        ) = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> list:
        """
        Build SQLAlchemy filter expressions.

        This method only constructs database conditions.
        It does not execute queries.

        All conditions are combined using AND semantics.

        Search itself uses OR semantics across the supported
        searchable fields.
        """

        conditions = []

        # --------------------------------------------------------------------
        # SEARCH
        # --------------------------------------------------------------------

        if search:
            normalized_search = (
                search.strip()
            )

            if normalized_search:
                pattern = (
                    f"%{normalized_search}%"
                )

                conditions.append(
                    or_(
                        Email.subject.ilike(
                            pattern,
                        ),
                        Email.sender.ilike(
                            pattern,
                        ),
                        Email.recipients.ilike(
                            pattern,
                        ),
                        Email.source_identifier.ilike(
                            pattern,
                        ),
                        Email.message_id.ilike(
                            pattern,
                        ),
                    )
                )

        # --------------------------------------------------------------------
        # SOURCE
        # --------------------------------------------------------------------

        if source is not None:
            conditions.append(
                Email.source == source
            )

        # --------------------------------------------------------------------
        # GROUND TRUTH / UI STATUS
        # --------------------------------------------------------------------

        if ground_truth_label is not None:
            conditions.append(
                Email.ground_truth_label
                == ground_truth_label
            )

        # --------------------------------------------------------------------
        # FROM DATE
        # --------------------------------------------------------------------

        if from_date is not None:
            conditions.append(
                Email.received_at >= from_date
            )

        # --------------------------------------------------------------------
        # TO DATE
        # --------------------------------------------------------------------

        if to_date is not None:
            conditions.append(
                Email.received_at <= to_date
            )

        return conditions

    # ========================================================================
    # PAGINATION HELPERS
    # ========================================================================

    @staticmethod
    def _normalize_page(
        page: int,
    ) -> int:
        """
        Normalize the requested page number.
        """

        try:
            normalized = int(page)
        except (
            TypeError,
            ValueError,
        ):
            normalized = 1

        return max(
            normalized,
            1,
        )

    @staticmethod
    def _normalize_page_size(
        page_size: int,
    ) -> int:
        """
        Normalize the requested page size.
        """

        try:
            normalized = int(
                page_size,
            )
        except (
            TypeError,
            ValueError,
        ):
            normalized = (
                DEFAULT_PAGE_SIZE
            )

        return max(
            1,
            min(
                normalized,
                MAX_PAGE_SIZE,
            ),
        )

    # ========================================================================
    # STATISTICS
    # ========================================================================

    def count_all(self) -> int:
        """
        Return the total number of stored emails.
        """

        statement = select(
            func.count(Email.id),
        )

        return int(
            self.db.scalar(
                statement,
            )
            or 0
        )

    def count_by_ground_truth(
        self,
        label: EmailGroundTruthLabel,
    ) -> int:
        """
        Return the number of emails assigned to one
        ground-truth label.
        """

        if label is None:
            return 0

        statement = (
            select(
                func.count(Email.id),
            )
            .where(
                Email.ground_truth_label
                == label
            )
        )

        return int(
            self.db.scalar(
                statement,
            )
            or 0
        )

    def get_statistics(
        self,
    ) -> dict[str, int]:
        """
        Return the statistics required by the
        Email Management UI.

        Result:

            {
                "total_emails": ...,
                "normal_emails": ...,
                "bombing_emails": ...,
            }
        """

        total = self.count_all()

        normal = self.count_by_ground_truth(
            EmailGroundTruthLabel.NORMAL,
        )

        bombing = self.count_by_ground_truth(
            EmailGroundTruthLabel.BOMBING,
        )

        return {
            "total_emails": total,
            "normal_emails": normal,
            "bombing_emails": bombing,
        }

    # ========================================================================
    # EXISTENCE
    # ========================================================================

    def exists(
        self,
        email_id: UUID,
    ) -> bool:
        """
        Return whether an email exists by UUID.
        """

        if email_id is None:
            return False

        statement = (
            select(
                func.count(Email.id),
            )
            .where(
                Email.id == email_id,
            )
        )

        return bool(
            self.db.scalar(
                statement,
            )
        )

    # ========================================================================
    # DUPLICATE DETECTION
    # ========================================================================

    def content_hash_exists(
        self,
        content_hash: str,
    ) -> bool:
        """
        Return whether the supplied content hash already exists.
        """

        if not content_hash:
            return False

        statement = (
            select(
                func.count(Email.id),
            )
            .where(
                Email.content_hash
                == content_hash,
            )
        )

        return bool(
            self.db.scalar(
                statement,
            )
        )

    # ========================================================================
    # DELETE
    # ========================================================================

    def delete(
        self,
        email: Email,
    ) -> None:
        """
        Delete one email from the current transaction.

        The service layer controls commit/rollback.
        """

        if email is None:
            return

        self.db.delete(email)
        self.db.flush()

    def delete_by_id(
        self,
        email_id: UUID,
    ) -> bool:
        """
        Delete an email by UUID.

        Returns:
            True  when an email was found and deleted.
            False when no matching email exists.
        """

        email = self.get_by_id(
            email_id,
        )

        if email is None:
            return False

        self.db.delete(email)
        self.db.flush()

        return True