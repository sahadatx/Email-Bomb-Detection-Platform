from __future__ import annotations

from datetime import date, datetime, time
from typing import TypedDict
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.modules.emails.models import (
    Email,
    EmailGroundTruthLabel,
    EmailSource,
)

from .models import ParsedEmail, ParsingStatus


# ============================================================
# CONSTANTS
# ============================================================

DEFAULT_PAGE_SIZE = 30
MAX_PAGE_SIZE = 100


# ============================================================
# SUMMARY TYPE
# ============================================================


class ParsingSummaryCounts(TypedDict):
    """
    Global parsing summary counts.

    These values represent the complete Module 03 state,
    not the currently visible UI page.
    """

    total_collected: int
    parsed: int
    pending: int
    warnings: int
    failed: int


# ============================================================
# REPOSITORY
# ============================================================


class ParsingRepository:
    """
    Repository for persistent Module 03 parsing results and the
    Parsing Workspace.

    Architectural rules
    -------------------
    1. Module 02 `emails` remains the canonical email source.
    2. Module 03 `parsed_emails` stores parsing results.
    3. There is at most one parsed result for each source email.
    4. Re-parsing uses upsert instead of creating duplicates.
    5. Parsing Workspace is based on Module 02 emails with a
       LEFT OUTER JOIN to Module 03 parsed results.
    6. Pending means an email exists in Module 02 but does not
       yet have a `parsed_emails` row.
    7. Level comes from Module 02 ground truth.
    8. Source comes from Module 02.
    9. Received date comes from Module 02.
    10. Parsing status comes from Module 03.
    11. Workspace filters use AND semantics between different
        filter fields.
    12. Search uses OR semantics across searchable email fields.
    13. Pagination is presentation-level and does not determine
        parsing batch size.
    """

    def __init__(
        self,
        db: Session,
    ) -> None:
        self.db = db

    # ========================================================
    # INTERNAL FILTER HELPERS
    # ========================================================

    @staticmethod
    def _normalize_page(
        page: int,
    ) -> int:
        """
        Normalize a page number to a valid positive value.
        """

        return max(
            page,
            1,
        )

    @staticmethod
    def _normalize_page_size(
        page_size: int,
    ) -> int:
        """
        Normalize the page size to the platform limits.
        """

        return min(
            max(
                page_size,
                1,
            ),
            MAX_PAGE_SIZE,
        )

    @staticmethod
    def _normalize_search(
        search: str | None,
    ) -> str | None:
        """
        Normalize a search string.

        Empty or whitespace-only values are treated as no
        search filter.
        """

        if search is None:
            return None

        normalized = search.strip()

        if not normalized:
            return None

        return normalized

    @staticmethod
    def _date_start(
        value: date,
    ) -> datetime:
        """
        Convert a date filter into the beginning of that day.

        The database stores received_at as a datetime, so date
        filters must cover the complete requested day.
        """

        return datetime.combine(
            value,
            time.min,
        )

    @staticmethod
    def _date_end(
        value: date,
    ) -> datetime:
        """
        Convert a date filter into the end of that day.
        """

        return datetime.combine(
            value,
            time.max,
        )

    def _build_workspace_conditions(
        self,
        *,
        search: str | None = None,
        source: EmailSource | None = None,
        level: EmailGroundTruthLabel | None = None,
        status: ParsingStatus | str | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list:
        """
        Build the common Parsing Workspace filter conditions.

        Important
        ---------
        Conditions across different filter fields are combined
        using AND semantics.

        Search is the exception: the individual searchable
        fields are combined using OR semantics inside one
        search condition.
        """

        conditions = []

        # ----------------------------------------------------
        # Search
        #
        # Search:
        #   Subject
        #   Sender
        #   Message-ID
        #   Source Identifier
        # ----------------------------------------------------

        normalized_search = self._normalize_search(
            search,
        )

        if normalized_search is not None:
            pattern = f"%{normalized_search}%"

            conditions.append(
                or_(
                    Email.subject.ilike(pattern),
                    Email.sender.ilike(pattern),
                    Email.message_id.ilike(pattern),
                    Email.source_identifier.ilike(pattern),
                )
            )

        # ----------------------------------------------------
        # Source
        # ----------------------------------------------------

        if source is not None:
            conditions.append(
                Email.source == source,
            )

        # ----------------------------------------------------
        # Level
        #
        # Ground truth is owned by Module 02.
        # ----------------------------------------------------

        if level is not None:
            conditions.append(
                Email.ground_truth_label == level,
            )

        # ----------------------------------------------------
        # Parsing status
        #
        # LEFT JOIN means PENDING has no ParsedEmail row.
        # Therefore status=PENDING is represented by
        # ParsedEmail.id IS NULL.
        # ----------------------------------------------------

        if status is not None:
            # PENDING is a workspace state, not a persisted
            # ParsedEmail status. The API schema includes it, while
            # the database enum intentionally only stores parsed,
            # warning, and failed rows.
            status_value = getattr(status, "value", status)

            if status_value == "pending":
                conditions.append(
                    ParsedEmail.id.is_(None),
                )
            else:
                conditions.append(
                    ParsedEmail.status
                    == ParsingStatus(status_value),
                )

        # ----------------------------------------------------
        # From date
        # ----------------------------------------------------

        if from_date is not None:
            conditions.append(
                Email.received_at
                >= self._date_start(from_date),
            )

        # ----------------------------------------------------
        # To date
        # ----------------------------------------------------

        if to_date is not None:
            conditions.append(
                Email.received_at
                <= self._date_end(to_date),
            )

        return conditions

    # ========================================================
    # GET BY PARSED RESULT ID
    # ========================================================

    def get_by_id(
        self,
        parsed_email_id: UUID,
    ) -> ParsedEmail | None:
        """
        Return a persisted parsed result by its own ID.
        """

        statement = (
            select(ParsedEmail)
            .where(
                ParsedEmail.id == parsed_email_id,
            )
        )

        return self.db.scalar(
            statement,
        )

    # ========================================================
    # GET BY SOURCE EMAIL ID
    # ========================================================

    def get_by_email_id(
        self,
        email_id: UUID,
    ) -> ParsedEmail | None:
        """
        Return the parsed result associated with a Module 02
        collected email.
        """

        statement = (
            select(ParsedEmail)
            .where(
                ParsedEmail.email_id == email_id,
            )
        )

        return self.db.scalar(
            statement,
        )

    # ========================================================
    # EXISTS
    # ========================================================

    def exists_for_email(
        self,
        email_id: UUID,
    ) -> bool:
        """
        Return True when a parsed result already exists for
        the supplied Module 02 email.
        """

        statement = select(
            select(ParsedEmail.id)
            .where(
                ParsedEmail.email_id == email_id,
            )
            .exists()
        )

        return bool(
            self.db.scalar(
                statement,
            )
        )

    # ========================================================
    # CREATE
    # ========================================================

    def create(
        self,
        parsed_email: ParsedEmail,
    ) -> ParsedEmail:
        """
        Persist a new parsed email result.

        The database unique constraint on `email_id` guarantees
        the one-to-one relationship with the source email.
        """

        self.db.add(
            parsed_email,
        )

        self.db.flush()
        self.db.refresh(
            parsed_email,
        )

        return parsed_email

    # ========================================================
    # UPDATE
    # ========================================================

    def update(
        self,
        parsed_email: ParsedEmail,
    ) -> ParsedEmail:
        """
        Persist changes to an existing parsed email result.
        """

        self.db.add(
            parsed_email,
        )

        self.db.flush()
        self.db.refresh(
            parsed_email,
        )

        return parsed_email

    # ========================================================
    # UPSERT
    # ========================================================

    def upsert(
        self,
        parsed_email: ParsedEmail,
    ) -> ParsedEmail:
        """
        Create or update the parsed result for a collected email.

        Re-parsing the same source email therefore updates the
        existing parsed result rather than creating a duplicate.
        """

        existing = self.get_by_email_id(
            parsed_email.email_id,
        )

        if existing is None:
            return self.create(
                parsed_email,
            )

        # ----------------------------------------------------
        # Parsed identity
        # ----------------------------------------------------

        existing.message_id = (
            parsed_email.message_id
        )

        existing.subject = (
            parsed_email.subject
        )

        existing.sender = (
            parsed_email.sender
        )

        existing.recipients = (
            parsed_email.recipients
        )

        existing.reply_to = (
            parsed_email.reply_to
        )

        existing.cc = (
            parsed_email.cc
        )

        existing.bcc = (
            parsed_email.bcc
        )

        existing.date = (
            parsed_email.date
        )

        # ----------------------------------------------------
        # Parsed structures
        # ----------------------------------------------------

        existing.headers = (
            parsed_email.headers
        )

        existing.text_body = (
            parsed_email.text_body
        )

        existing.html_body = (
            parsed_email.html_body
        )

        existing.mime_parts = (
            parsed_email.mime_parts
        )

        existing.attachments = (
            parsed_email.attachments
        )

        # ----------------------------------------------------
        # Validation
        # ----------------------------------------------------

        existing.validation_errors = (
            parsed_email.validation_errors
        )

        existing.validation_warnings = (
            parsed_email.validation_warnings
        )

        # ----------------------------------------------------
        # Processing state
        # ----------------------------------------------------

        existing.status = (
            parsed_email.status
        )

        existing.parser_version = (
            parsed_email.parser_version
        )

        existing.processing_time_ms = (
            parsed_email.processing_time_ms
        )

        existing.parsed_at = (
            parsed_email.parsed_at
        )

        existing.updated_at = (
            parsed_email.updated_at
        )

        self.db.flush()
        self.db.refresh(
            existing,
        )

        return existing

    # ========================================================
    # LIST PARSED RESULTS
    # ========================================================

    def list(
        self,
        *,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
        status: ParsingStatus | str | None = None,
    ) -> tuple[list[ParsedEmail], int]:
        """
        Return paginated persisted parsed results.

        This method preserves the original repository contract
        and operates directly on `parsed_emails`.

        The Parsing Workspace should use `list_workspace()`
        because the workspace also needs pending emails.
        """

        page = self._normalize_page(
            page,
        )

        page_size = self._normalize_page_size(
            page_size,
        )

        offset = (
            (page - 1)
            * page_size
        )

        conditions = []

        if status is not None:
            conditions.append(
                ParsedEmail.status == status,
            )

        # ----------------------------------------------------
        # Items
        # ----------------------------------------------------

        items_statement = (
            select(ParsedEmail)
            .where(*conditions)
            .order_by(
                ParsedEmail.created_at.desc(),
                ParsedEmail.id.desc(),
            )
            .offset(offset)
            .limit(page_size)
        )

        items = list(
            self.db.scalars(
                items_statement,
            ).all()
        )

        # ----------------------------------------------------
        # Total
        # ----------------------------------------------------

        count_statement = (
            select(
                func.count(
                    ParsedEmail.id,
                ),
            )
            .where(*conditions)
        )

        total = (
            self.db.scalar(
                count_statement,
            )
            or 0
        )

        return (
            items,
            int(total),
        )

    # ========================================================
    # LIST PARSING WORKSPACE
    # ========================================================

    def list_workspace(
        self,
        *,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
        search: str | None = None,
        source: EmailSource | None = None,
        level: EmailGroundTruthLabel | None = None,
        status: ParsingStatus | str | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> tuple[list[tuple[Email, ParsedEmail | None]], int]:
        """
        Return the paginated Parsing Workspace.

        The workspace is based on:

            Email
                LEFT OUTER JOIN
            ParsedEmail

        This is required because pending emails do not have a
        ParsedEmail row yet.

        Each item is returned as:

            (
                Email,
                ParsedEmail | None,
            )

        Therefore:

            ParsedEmail is None
                -> PENDING

            ParsedEmail exists
                -> use ParsedEmail.status
        """

        page = self._normalize_page(
            page,
        )

        page_size = self._normalize_page_size(
            page_size,
        )

        offset = (
            (page - 1)
            * page_size
        )

        conditions = self._build_workspace_conditions(
            search=search,
            source=source,
            level=level,
            status=status,
            from_date=from_date,
            to_date=to_date,
        )

        # ----------------------------------------------------
        # Items
        # ----------------------------------------------------

        items_statement = (
            select(
                Email,
                ParsedEmail,
            )
            .outerjoin(
                ParsedEmail,
                ParsedEmail.email_id == Email.id,
            )
            .where(
                *conditions,
            )
            .order_by(
                Email.created_at.desc(),
                Email.id.desc(),
            )
            .offset(offset)
            .limit(page_size)
        )

        rows = list(
            self.db.execute(
                items_statement,
            ).all()
        )

        # ----------------------------------------------------
        # Total
        #
        # Count Email.id rather than ParsedEmail.id because
        # pending emails have no ParsedEmail row.
        # ----------------------------------------------------

        count_statement = (
            select(
                func.count(
                    Email.id,
                ),
            )
            .select_from(
                Email,
            )
            .outerjoin(
                ParsedEmail,
                ParsedEmail.email_id == Email.id,
            )
            .where(
                *conditions,
            )
        )

        total = int(
            self.db.scalar(
                count_statement,
            )
            or 0
        )

        return (
            rows,
            total,
        )

    # ========================================================
    # GET MATCHING EMAIL IDS
    # ========================================================

    def get_matching_email_ids(
        self,
        *,
        search: str | None = None,
        source: EmailSource | None = None,
        level: EmailGroundTruthLabel | None = None,
        status: ParsingStatus | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[UUID]:
        """
        Return every source email ID matching the supplied
        Parsing Workspace filters.

        This method intentionally does not apply pagination.

        It is used by bulk operations such as:

            Select All Matching
            Parse All Matching
            Parse All Pending
        """

        conditions = self._build_workspace_conditions(
            search=search,
            source=source,
            level=level,
            status=status,
            from_date=from_date,
            to_date=to_date,
        )

        statement = (
            select(
                Email.id,
            )
            .select_from(
                Email,
            )
            .outerjoin(
                ParsedEmail,
                ParsedEmail.email_id == Email.id,
            )
            .where(
                *conditions,
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

    # ========================================================
    # GET PENDING EMAIL IDS
    # ========================================================

    def get_pending_email_ids(
        self,
        *,
        search: str | None = None,
        source: EmailSource | None = None,
        level: EmailGroundTruthLabel | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[UUID]:
        """
        Return all currently pending source email IDs.

        Pending means:

            Email exists
            AND
            ParsedEmail does not exist

        This method does not apply pagination.
        """

        return self.get_matching_email_ids(
            search=search,
            source=source,
            level=level,
            # Pass the workspace-only value. Do not add PENDING to
            # the persistence enum: pending means no parsed row exists.
            status="pending",
            from_date=from_date,
            to_date=to_date,
        )

    # ========================================================
    # GET EMAILS BY IDS
    # ========================================================

    def get_emails_by_ids(
        self,
        email_ids: list[UUID],
    ) -> list[Email]:
        """
        Return Module 02 emails for the supplied IDs.

        The result follows the order defined by the database
        query, not necessarily the input list order.
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

    # ========================================================
    # GET PARSED EMAILS BY IDS
    # ========================================================

    def get_parsed_emails_by_email_ids(
        self,
        email_ids: list[UUID],
    ) -> list[ParsedEmail]:
        """
        Return persisted parsing results for source email IDs.

        Pending emails are naturally absent from this result.
        """

        if not email_ids:
            return []

        statement = (
            select(ParsedEmail)
            .where(
                ParsedEmail.email_id.in_(email_ids),
            )
            .order_by(
                ParsedEmail.created_at.desc(),
                ParsedEmail.id.desc(),
            )
        )

        return list(
            self.db.scalars(
                statement,
            ).all()
        )

    # ========================================================
    # COUNT
    # ========================================================

    def count(
        self,
        *,
        status: ParsingStatus | None = None,
    ) -> int:
        """
        Return the number of persisted parsed results.

        When status is omitted, all parsed_emails rows are counted.
        """

        statement = select(
            func.count(
                ParsedEmail.id,
            ),
        )

        if status is not None:
            statement = statement.where(
                ParsedEmail.status == status,
            )

        return int(
            self.db.scalar(
                statement,
            )
            or 0
        )

    # ========================================================
    # COUNT BY STATUS
    # ========================================================

    def count_by_status(
        self,
        status: ParsingStatus,
    ) -> int:
        """
        Return the number of persisted parsed results having
        the supplied parsing status.
        """

        return self.count(
            status=status,
        )

    # ========================================================
    # STATUS COUNTS
    # ========================================================

    def get_status_counts(
        self,
    ) -> dict[str, int]:
        """
        Return counts for all persisted parsing statuses.

        Pending is intentionally calculated separately because
        pending emails do not have a parsed_emails row.
        """

        statement = (
            select(
                ParsedEmail.status,
                func.count(
                    ParsedEmail.id,
                ),
            )
            .group_by(
                ParsedEmail.status,
            )
        )

        rows = self.db.execute(
            statement,
        ).all()

        counts = {
            ParsingStatus.PARSED.value: 0,
            ParsingStatus.WARNING.value: 0,
            ParsingStatus.FAILED.value: 0,
        }

        for status, count in rows:
            if status is None:
                continue

            status_value = (
                status.value
                if isinstance(
                    status,
                    ParsingStatus,
                )
                else str(status)
            )

            if status_value in counts:
                counts[status_value] = int(
                    count,
                )

        return counts

    # ========================================================
    # COUNT PENDING
    # ========================================================

    def count_pending(
        self,
    ) -> int:
        """
        Return the number of collected emails that do not yet
        have a persisted parsed result.
        """

        statement = (
            select(
                func.count(
                    Email.id,
                ),
            )
            .select_from(
                Email,
            )
            .outerjoin(
                ParsedEmail,
                ParsedEmail.email_id == Email.id,
            )
            .where(
                ParsedEmail.id.is_(None),
            )
        )

        return int(
            self.db.scalar(
                statement,
            )
            or 0
        )

    # ========================================================
    # GLOBAL SUMMARY
    # ========================================================

    def get_summary_counts(
        self,
    ) -> ParsingSummaryCounts:
        """
        Return the complete global Module 03 parsing summary.

        Definitions
        -----------
        total_collected:
            Total number of emails collected by Module 02.

        parsed:
            Persisted parsed results with status `parsed`.

        pending:
            Module 02 emails that do not yet have a parsed result.

        warnings:
            Persisted parsed results with status `warning`.

        failed:
            Persisted parsed results with status `failed`.

        This summary is global state and is independent of
        workspace pagination and filters.
        """

        # ----------------------------------------------------
        # Total Module 02 emails
        # ----------------------------------------------------

        total_collected_statement = select(
            func.count(
                Email.id,
            ),
        )

        total_collected = int(
            self.db.scalar(
                total_collected_statement,
            )
            or 0
        )

        # ----------------------------------------------------
        # Persisted parsing status counts
        # ----------------------------------------------------

        status_counts = (
            self.get_status_counts()
        )

        parsed = status_counts[
            ParsingStatus.PARSED.value
        ]

        warnings = status_counts[
            ParsingStatus.WARNING.value
        ]

        failed = status_counts[
            ParsingStatus.FAILED.value
        ]

        # ----------------------------------------------------
        # Pending
        #
        # Calculate directly using the LEFT JOIN definition.
        # This avoids deriving pending from potentially inconsistent
        # status totals.
        # ----------------------------------------------------

        pending = self.count_pending()

        return {
            "total_collected": total_collected,
            "parsed": parsed,
            "pending": pending,
            "warnings": warnings,
            "failed": failed,
        }

    # ========================================================
    # DELETE
    # ========================================================

    def delete(
        self,
        parsed_email: ParsedEmail,
    ) -> None:
        """
        Delete a persisted parsed result.

        This method is retained for repository compatibility
        and controlled reprocessing workflows.

        Deleting a parsed result makes the source email pending
        again from the Parsing Workspace perspective.
        """

        self.db.delete(
            parsed_email,
        )

        self.db.flush()
