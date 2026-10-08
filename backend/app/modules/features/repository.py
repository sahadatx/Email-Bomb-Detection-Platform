from __future__ import annotations

from datetime import date, datetime, time, timezone
from typing import Sequence
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.modules.emails.models import Email
from app.modules.features.models import (
    EmailFeatures,
    FeatureExtractionStatus,
)
from app.modules.features.schemas import FeatureWorkspaceFilters
from app.modules.parsing.models import (
    ParsedEmail,
    ParsingStatus as SourceParsingStatus,
)


# ============================================================
# CONSTANTS
# ============================================================

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 30
MAX_PAGE_SIZE = 100


# ============================================================
# REPOSITORY
# ============================================================


class FeatureRepository:
    """
    Database access layer for Module 04 — Feature Engineering.

    Responsibilities
    ----------------
    - Canonical email lookup
    - Parsed email lookup
    - Feature record lookup
    - Feature create/update/delete
    - Feature upsert
    - Feature Workspace filtering
    - Feature Workspace pagination
    - Global filtered selection
    - Temporal timestamp retrieval
    - Feature status counts
    - Pending feature counts
    - Extraction eligibility
    - Feature extraction failure persistence

    Module Boundary
    ---------------
    Module 04 operates only on successfully parsed emails.

    Canonical Feature Workspace population:

        ParsedEmail
            INNER JOIN
        Email
            LEFT JOIN
        EmailFeatures

    Therefore:

        Module 02 Email
            ↓
        Module 03 ParsedEmail
            ↓
        Module 04 EmailFeatures

    Unparsed emails are never Feature Engineering candidates.

    Pending Semantics
    -----------------
    A record is pending when:

        ParsedEmail exists
        AND
        EmailFeatures does not exist

    Selection Semantics
    -------------------
    "Select All Matching" operates on the COMPLETE filtered
    Feature Workspace result set, not only the currently
    displayed pagination page.

    Therefore:

        page_size = 30
        filtered_total = 347

    may produce:

        displayed rows = 30
        selectable rows = all matching selectable rows

    Extracted feature records are not selectable because their
    canonical F1-F12 vector already exists.

    Temporal Semantics
    -----------------
    F11 and F12 use received_at values from the complete
    collected-email population.

    Explicitly Excluded
    -------------------
    - F1-F12 calculation logic
    - Feature extraction logic
    - ML
    - Classification
    - Prediction
    - Confidence
    - Risk scoring
    - Threat scoring
    """

    def __init__(
        self,
        db: Session,
    ) -> None:
        self.db = db

    # ========================================================
    # PAGINATION HELPERS
    # ========================================================

    @staticmethod
    def _normalize_page(
        page: int,
    ) -> int:
        """
        Normalize page number.

        Values below 1 are converted to page 1.
        """

        return max(
            DEFAULT_PAGE,
            int(page),
        )

    @staticmethod
    def _normalize_page_size(
        page_size: int,
    ) -> int:
        """
        Normalize page size.

        Page size is always constrained to:

            1 <= page_size <= MAX_PAGE_SIZE
        """

        return min(
            max(
                1,
                int(page_size),
            ),
            MAX_PAGE_SIZE,
        )

    # ========================================================
    # FILTER HELPERS
    # ========================================================

    @staticmethod
    def _normalize_search(
        value: str | None,
    ) -> str | None:
        """
        Normalize workspace search text.

        Empty or whitespace-only values become None.
        """

        if value is None:
            return None

        normalized = value.strip()

        return normalized or None

    @staticmethod
    def _normalize_filter_value(
        value: str | None,
    ) -> str | None:
        """
        Normalize enum-like filter values.

        Example:

            "  RAW_EMAIL "
                ->
            "raw_email"
        """

        if value is None:
            return None

        normalized = value.strip().lower()

        return normalized or None

    @staticmethod
    def _start_of_day(
        value: date,
    ) -> datetime:
        """
        Convert a date into an inclusive lower datetime
        boundary.

        Example:

            2026-09-25
                ->
            2026-09-25 00:00:00
        """

        return datetime.combine(
            value,
            time.min,
        )

    @staticmethod
    def _end_of_day(
        value: date,
    ) -> datetime:
        """
        Convert a date into an inclusive upper datetime
        boundary.

        Example:

            2026-09-25
                ->
            2026-09-25 23:59:59.999999
        """

        return datetime.combine(
            value,
            time.max,
        )

    # ========================================================
    # EMAIL LOOKUP
    # ========================================================

    def get_email(
        self,
        email_id: UUID,
    ) -> Email | None:
        """
        Return the canonical Module 02 email.
        """

        statement = (
            select(Email)
            .where(
                Email.id == email_id,
            )
        )

        return self.db.scalar(
            statement,
        )

    def get_emails(
        self,
        email_ids: Sequence[UUID],
    ) -> list[Email]:
        """
        Return canonical emails matching supplied IDs.

        Results are returned in deterministic creation order.
        """

        if not email_ids:
            return []

        statement = (
            select(Email)
            .where(
                Email.id.in_(
                    list(email_ids),
                ),
            )
            .order_by(
                Email.created_at.asc(),
                Email.id.asc(),
            )
        )

        return list(
            self.db.scalars(
                statement,
            ).all(),
        )

    def get_all_emails(
        self,
    ) -> list[Email]:
        """
        Return all collected emails.

        Used by temporal extraction for:

            F11 — Emails Per Minute
            F12 — Emails Per Hour
        """

        statement = (
            select(Email)
            .order_by(
                Email.created_at.asc(),
                Email.id.asc(),
            )
        )

        return list(
            self.db.scalars(
                statement,
            ).all(),
        )

    def email_exists(
        self,
        email_id: UUID,
    ) -> bool:
        """
        Determine whether a canonical email exists.
        """

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
            or 0,
        )

    # ========================================================
    # PARSED EMAIL LOOKUP
    # ========================================================

    def get_parsed_email(
        self,
        email_id: UUID,
    ) -> ParsedEmail | None:
        """
        Return the Module 03 parsed representation.
        """

        statement = (
            select(ParsedEmail)
            .where(
                ParsedEmail.email_id
                == email_id,
            )
        )

        return self.db.scalar(
            statement,
        )

    def get_parsed_emails(
        self,
        email_ids: Sequence[UUID],
    ) -> list[ParsedEmail]:
        """
        Return parsed representations for supplied email IDs.
        """

        if not email_ids:
            return []

        statement = (
            select(ParsedEmail)
            .where(
                ParsedEmail.email_id.in_(
                    list(email_ids),
                ),
            )
            .order_by(
                ParsedEmail.created_at.asc(),
                ParsedEmail.id.asc(),
            )
        )

        return list(
            self.db.scalars(
                statement,
            ).all(),
        )

    def parsed_email_exists(
        self,
        email_id: UUID,
    ) -> bool:
        """
        Determine whether an email has been successfully parsed.
        """

        statement = (
            select(
                func.count(
                    ParsedEmail.id,
                ),
            )
            .where(
                ParsedEmail.email_id
                == email_id,
            )
        )

        return bool(
            self.db.scalar(
                statement,
            )
            or 0,
        )

    # ========================================================
    # FEATURE LOOKUP
    # ========================================================

    def get_feature(
        self,
        email_id: UUID,
    ) -> EmailFeatures | None:
        """
        Return the current Module 04 feature record.
        """

        statement = (
            select(EmailFeatures)
            .where(
                EmailFeatures.email_id
                == email_id,
            )
        )

        return self.db.scalar(
            statement,
        )

    def get_features_by_ids(
        self,
        email_ids: Sequence[UUID],
    ) -> list[EmailFeatures]:
        """
        Return feature records for supplied email IDs.
        """

        if not email_ids:
            return []

        statement = (
            select(EmailFeatures)
            .where(
                EmailFeatures.email_id.in_(
                    list(email_ids),
                ),
            )
            .order_by(
                EmailFeatures.created_at.asc(),
                EmailFeatures.id.asc(),
            )
        )

        return list(
            self.db.scalars(
                statement,
            ).all(),
        )

    def feature_exists(
        self,
        email_id: UUID,
    ) -> bool:
        """
        Determine whether an EmailFeatures record exists.
        """

        statement = (
            select(
                func.count(
                    EmailFeatures.id,
                ),
            )
            .where(
                EmailFeatures.email_id
                == email_id,
            )
        )

        return bool(
            self.db.scalar(
                statement,
            )
            or 0,
        )

    # ========================================================
    # FEATURE CREATE / UPDATE
    # ========================================================

    def upsert_features(
        self,
        email_id: UUID,
        *,
        f1_sender_email: str | None,
        f2_known_domain: bool,
        f3_message_id: bool,
        f4_auto_submitted: bool,
        f5_precedence_bulk: bool,
        f6_list_id: bool,
        f7_x_beenthere: bool,
        f8_x_anti_abuse: bool,
        f9_keyword_features: int,
        f10_subject_length: int,
        f11_emails_per_minute: int,
        f12_emails_per_hour: int,
        feature_vector: dict[str, object],
        validation_errors: list[str],
        validation_warnings: list[str],
        status: FeatureExtractionStatus,
        extractor_version: str,
        processing_time_ms: int,
        extracted_at: datetime,
    ) -> EmailFeatures:
        """
        Create or update the single current feature record
        belonging to an email.

        There is exactly one EmailFeatures record per email.
        """

        feature = self.get_feature(
            email_id,
        )

        now = datetime.now(
            timezone.utc,
        )

        normalized_processing_time = max(
            0,
            processing_time_ms,
        )

        normalized_feature_vector = dict(
            feature_vector,
        )

        normalized_errors = list(
            validation_errors,
        )

        normalized_warnings = list(
            validation_warnings,
        )

        # ----------------------------------------------------
        # CREATE
        # ----------------------------------------------------

        if feature is None:
            feature = EmailFeatures(
                email_id=email_id,

                # F1-F8
                f1_sender_email=f1_sender_email,
                f2_known_domain=f2_known_domain,
                f3_message_id=f3_message_id,
                f4_auto_submitted=f4_auto_submitted,
                f5_precedence_bulk=f5_precedence_bulk,
                f6_list_id=f6_list_id,
                f7_x_beenthere=f7_x_beenthere,
                f8_x_anti_abuse=f8_x_anti_abuse,

                # F9-F12
                f9_keyword_features=max(
                    0,
                    f9_keyword_features,
                ),
                f10_subject_length=max(
                    0,
                    f10_subject_length,
                ),
                f11_emails_per_minute=max(
                    0,
                    f11_emails_per_minute,
                ),
                f12_emails_per_hour=max(
                    0,
                    f12_emails_per_hour,
                ),

                # Vector
                feature_vector=(
                    normalized_feature_vector
                ),

                # Validation
                validation_errors=(
                    normalized_errors
                ),
                validation_warnings=(
                    normalized_warnings
                ),

                # Metadata
                status=status,
                extractor_version=(
                    extractor_version
                ),
                processing_time_ms=(
                    normalized_processing_time
                ),
                extracted_at=extracted_at,

                created_at=now,
                updated_at=now,
            )

            self.db.add(
                feature,
            )

            self.db.flush()

            return feature

        # ----------------------------------------------------
        # UPDATE
        # ----------------------------------------------------

        feature.f1_sender_email = (
            f1_sender_email
        )

        feature.f2_known_domain = (
            f2_known_domain
        )

        feature.f3_message_id = (
            f3_message_id
        )

        feature.f4_auto_submitted = (
            f4_auto_submitted
        )

        feature.f5_precedence_bulk = (
            f5_precedence_bulk
        )

        feature.f6_list_id = (
            f6_list_id
        )

        feature.f7_x_beenthere = (
            f7_x_beenthere
        )

        feature.f8_x_anti_abuse = (
            f8_x_anti_abuse
        )

        feature.f9_keyword_features = max(
            0,
            f9_keyword_features,
        )

        feature.f10_subject_length = max(
            0,
            f10_subject_length,
        )

        feature.f11_emails_per_minute = max(
            0,
            f11_emails_per_minute,
        )

        feature.f12_emails_per_hour = max(
            0,
            f12_emails_per_hour,
        )

        feature.feature_vector = (
            normalized_feature_vector
        )

        feature.validation_errors = (
            normalized_errors
        )

        feature.validation_warnings = (
            normalized_warnings
        )

        feature.status = status

        feature.extractor_version = (
            extractor_version
        )

        feature.processing_time_ms = (
            normalized_processing_time
        )

        feature.extracted_at = extracted_at

        feature.updated_at = now

        self.db.flush()

        return feature

    # ========================================================
    # FEATURE DELETE
    # ========================================================

    def delete_features(
        self,
        email_id: UUID,
    ) -> bool:
        """
        Delete only the Module 04 feature record.

        Module 02 Email and Module 03 ParsedEmail remain
        untouched.
        """

        feature = self.get_feature(
            email_id,
        )

        if feature is None:
            return False

        self.db.delete(
            feature,
        )

        self.db.flush()

        return True

    # ========================================================
    # EMAIL COUNTS
    # ========================================================

    def count_emails(
        self,
    ) -> int:
        """
        Count all collected emails.
        """

        statement = select(
            func.count(
                Email.id,
            ),
        )

        return int(
            self.db.scalar(
                statement,
            )
            or 0,
        )

    def count_parsed_emails(
        self,
    ) -> int:
        """
        Count successfully parsed emails.

        This is the authoritative Module 04 candidate
        population.
        """

        statement = select(
            func.count(
                ParsedEmail.id,
            ),
        ).where(
            ParsedEmail.status.in_(
                [
                    SourceParsingStatus.PARSED,
                    SourceParsingStatus.WARNING,
                ],
            ),
        )

        return int(
            self.db.scalar(
                statement,
            )
            or 0,
        )

    def count_feature_records(
        self,
    ) -> int:
        """
        Count persisted EmailFeatures records.
        """

        statement = select(
            func.count(
                EmailFeatures.id,
            ),
        )

        return int(
            self.db.scalar(
                statement,
            )
            or 0,
        )

    # ========================================================
    # GENERIC EMAIL PAGINATION
    # ========================================================

    def list_email_page(
        self,
        *,
        page: int = DEFAULT_PAGE,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> tuple[
        list[Email],
        int,
    ]:
        """
        Return paginated canonical Module 02 emails.

        This represents all collected emails and is separate
        from the Feature Workspace candidate population.
        """

        page = self._normalize_page(
            page,
        )

        page_size = self._normalize_page_size(
            page_size,
        )

        total = self.count_emails()

        offset = (
            page - 1
        ) * page_size

        statement = (
            select(Email)
            .order_by(
                Email.created_at.asc(),
                Email.id.asc(),
            )
            .offset(offset)
            .limit(page_size)
        )

        items = list(
            self.db.scalars(
                statement,
            ).all(),
        )

        return items, total

    # ========================================================
    # FEATURE WORKSPACE FILTER CONDITIONS
    # ========================================================

    def _build_feature_workspace_conditions(
        self,
        filters: FeatureWorkspaceFilters | None,
    ) -> list[object]:
        """
        Build SQLAlchemy WHERE conditions for Feature Workspace.

        All populated filters use AND semantics.

        Search fields:

            subject
            sender
            Message-ID
            source identifier

        Exact dimensions:

            source
            level
            status

        Date dimensions:

            from_date
            to_date
        """

        conditions: list[object] = [
            ParsedEmail.status.in_(
                [
                    SourceParsingStatus.PARSED,
                    SourceParsingStatus.WARNING,
                ],
            ),
        ]

        if filters is None:
            return conditions

        # ----------------------------------------------------
        # SEARCH
        # ----------------------------------------------------

        search = self._normalize_search(
            filters.search,
        )

        if search is not None:
            search_pattern = (
                f"%{search}%"
            )

            conditions.append(
                or_(
                    Email.subject.ilike(
                        search_pattern,
                    ),
                    Email.sender.ilike(
                        search_pattern,
                    ),
                    Email.message_id.ilike(
                        search_pattern,
                    ),
                    Email.source_identifier.ilike(
                        search_pattern,
                    ),
                ),
            )

        # ----------------------------------------------------
        # SOURCE
        # ----------------------------------------------------

        source = self._normalize_filter_value(
            filters.source,
        )

        if source is not None:
            conditions.append(
                func.lower(
                    Email.source,
                )
                == source,
            )

        # ----------------------------------------------------
        # LEVEL
        # ----------------------------------------------------

        level = self._normalize_filter_value(
            filters.level,
        )

        if level is not None:
            conditions.append(
                func.lower(
                    Email.ground_truth_label,
                )
                == level,
            )

        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        feature_status = (
            self._normalize_filter_value(
                filters.status,
            )
        )

        if feature_status == "pending":

            conditions.append(
                EmailFeatures.id.is_(None),
            )

        elif feature_status in {
            "extracted",
            "warning",
            "failed",
        }:

            conditions.append(
                EmailFeatures.status
                == feature_status,
            )

        # ----------------------------------------------------
        # FROM DATE
        # ----------------------------------------------------

        if filters.from_date is not None:
            conditions.append(
                Email.received_at
                >= self._start_of_day(
                    filters.from_date,
                ),
            )

        # ----------------------------------------------------
        # TO DATE
        # ----------------------------------------------------

        if filters.to_date is not None:
            conditions.append(
                Email.received_at
                <= self._end_of_day(
                    filters.to_date,
                ),
            )

        return conditions

    # ========================================================
    # FEATURE WORKSPACE BASE QUERY
    # ========================================================

    @staticmethod
    def _feature_workspace_select():
        """
        Build the canonical Feature Workspace query.

        Root:

            ParsedEmail

        INNER JOIN:

            Email

        LEFT JOIN:

            EmailFeatures

        This guarantees that unparsed emails never enter
        Module 04.
        """

        return (
            select(
                Email,
                ParsedEmail,
                EmailFeatures,
            )
            .select_from(
                ParsedEmail,
            )
            .join(
                Email,
                Email.id
                == ParsedEmail.email_id,
            )
            .outerjoin(
                EmailFeatures,
                EmailFeatures.email_id
                == ParsedEmail.email_id,
            )
        )

    # ========================================================
    # FEATURE WORKSPACE COUNT
    # ========================================================

    def count_feature_workspace(
        self,
        *,
        filters: FeatureWorkspaceFilters | None = None,
    ) -> int:
        """
        Count the COMPLETE filtered Feature Workspace.

        IMPORTANT
        ---------
        This is NOT the current page count.

        Example:

            page_size = 30
            filtered_total = 347

        returns:

            347

        The same filters and candidate population used by
        list_feature_page() are used here.
        """

        conditions = (
            self._build_feature_workspace_conditions(
                filters,
            )
        )

        statement = (
            select(
                func.count(
                    ParsedEmail.id,
                ),
            )
            .select_from(
                ParsedEmail,
            )
            .join(
                Email,
                Email.id
                == ParsedEmail.email_id,
            )
            .outerjoin(
                EmailFeatures,
                EmailFeatures.email_id
                == ParsedEmail.email_id,
            )
        )

        if conditions:
            statement = statement.where(
                and_(*conditions),
            )

        return int(
            self.db.scalar(
                statement,
            )
            or 0,
        )

    # ========================================================
    # FEATURE WORKSPACE PAGINATION
    # ========================================================

    def list_feature_page(
        self,
        *,
        page: int = DEFAULT_PAGE,
        page_size: int = DEFAULT_PAGE_SIZE,
        filters: FeatureWorkspaceFilters | None = None,
    ) -> tuple[
        list[
            tuple[
                Email,
                ParsedEmail,
                EmailFeatures | None,
            ]
        ],
        int,
    ]:
        """
        Return one filtered Feature Workspace page.

        IMPORTANT
        ---------
        `total` is the COMPLETE filtered result count.

        Pagination only controls which rows are displayed.

        Returned row:

            (
                Email,
                ParsedEmail,
                EmailFeatures | None,
            )

        Pending:

            EmailFeatures is None

        Extracted / Warning / Failed:

            EmailFeatures exists with matching status
        """

        page = self._normalize_page(
            page,
        )

        page_size = self._normalize_page_size(
            page_size,
        )

        conditions = (
            self._build_feature_workspace_conditions(
                filters,
            )
        )

        total = self.count_feature_workspace(
            filters=filters,
        )

        offset = (
            page - 1
        ) * page_size

        statement = (
            self._feature_workspace_select()
        )

        if conditions:
            statement = statement.where(
                and_(*conditions),
            )

        statement = (
            statement
            .order_by(
                Email.received_at.desc().nullslast(),
                Email.created_at.desc(),
                Email.id.desc(),
            )
            .offset(offset)
            .limit(page_size)
        )

        rows = list(
            self.db.execute(
                statement,
            ).all(),
        )

        return rows, total

    # ========================================================
    # GLOBAL SELECTABLE EMAIL IDS
    # ========================================================

    def list_selectable_feature_email_ids(
        self,
        *,
        filters: FeatureWorkspaceFilters | None = None,
    ) -> list[UUID]:
        """
        Return ALL selectable email IDs matching the supplied
        Feature Workspace filters.

        This method intentionally does NOT apply pagination.

        It powers:

            "Select All Matching"

        Selection population:

            ParsedEmail
                INNER JOIN Email
                LEFT JOIN EmailFeatures

        Selectable rule:

            ParsedEmail exists
            AND
            EmailFeatures does not exist

        OR:

            EmailFeatures exists with:

                warning
                failed

        Extracted records are excluded.

        Therefore:

            pending
            warning
            failed

        are selectable.

        Important
        ---------
        The returned IDs represent the COMPLETE filtered
        matching population, not just the current UI page.
        """

        conditions = (
            self._build_feature_workspace_conditions(
                filters,
            )
        )

        # ----------------------------------------------------
        # Selection-specific eligibility.
        #
        # A complete extracted vector is not selectable.
        #
        # Pending:
        #     no EmailFeatures
        #
        # Warning:
        #     EmailFeatures.status = warning
        #
        # Failed:
        #     EmailFeatures.status = failed
        # ----------------------------------------------------

        selectable_condition = or_(
            EmailFeatures.id.is_(None),
            EmailFeatures.status.in_(
                [
                    FeatureExtractionStatus.WARNING,
                    FeatureExtractionStatus.FAILED,
                ],
            ),
        )

        conditions.append(
            selectable_condition,
        )

        statement = (
            select(
                Email.id,
            )
            .select_from(
                ParsedEmail,
            )
            .join(
                Email,
                Email.id
                == ParsedEmail.email_id,
            )
            .outerjoin(
                EmailFeatures,
                EmailFeatures.email_id
                == ParsedEmail.email_id,
            )
            .where(
                and_(*conditions),
            )
            .order_by(
                Email.received_at.desc().nullslast(),
                Email.created_at.desc(),
                Email.id.desc(),
            )
        )

        return list(
            self.db.scalars(
                statement,
            ).all(),
        )

    # ========================================================
    # GLOBAL SELECTABLE COUNT
    # ========================================================

    def count_selectable_feature_emails(
        self,
        *,
        filters: FeatureWorkspaceFilters | None = None,
    ) -> int:
        """
        Count ALL selectable emails matching the supplied
        Feature Workspace filters.

        This count is intentionally independent from pagination.

        Example:

            filtered workspace = 347
            extracted = 35
            selectable = 312

        returns:

            312
        """

        conditions = (
            self._build_feature_workspace_conditions(
                filters,
            )
        )

        selectable_condition = or_(
            EmailFeatures.id.is_(None),
            EmailFeatures.status.in_(
                [
                    FeatureExtractionStatus.WARNING,
                    FeatureExtractionStatus.FAILED,
                ],
            ),
        )

        conditions.append(
            selectable_condition,
        )

        statement = (
            select(
                func.count(
                    ParsedEmail.id,
                ),
            )
            .select_from(
                ParsedEmail,
            )
            .join(
                Email,
                Email.id
                == ParsedEmail.email_id,
            )
            .outerjoin(
                EmailFeatures,
                EmailFeatures.email_id
                == ParsedEmail.email_id,
            )
            .where(
                and_(*conditions),
            )
        )

        return int(
            self.db.scalar(
                statement,
            )
            or 0,
        )

    # ========================================================
    # TEMPORAL DATA
    # ========================================================

    def get_received_at_values(
        self,
    ) -> list[datetime | None]:
        """
        Return received_at values for ALL collected emails.

        Used by temporal.py for:

            F11 — Emails Per Minute
            F12 — Emails Per Hour

        This intentionally does NOT use:

            - current page
            - Feature Workspace filters
            - parsed-only population
            - selected IDs

        Temporal extraction remains based on the complete
        collection timeline.
        """

        statement = (
            select(
                Email.received_at,
            )
            .order_by(
                Email.received_at.asc(),
                Email.id.asc(),
            )
        )

        return list(
            self.db.scalars(
                statement,
            ).all(),
        )

    # ========================================================
    # FEATURE STATUS COUNTS
    # ========================================================

    def count_feature_status(
        self,
        status: FeatureExtractionStatus,
    ) -> int:
        """
        Count persisted feature records by extraction status.
        """

        statement = (
            select(
                func.count(
                    EmailFeatures.id,
                ),
            )
            .join(
                ParsedEmail,
                ParsedEmail.email_id
                == EmailFeatures.email_id,
            )
            .where(
                EmailFeatures.status == status,
                ParsedEmail.status.in_(
                    [
                        SourceParsingStatus.PARSED,
                        SourceParsingStatus.WARNING,
                    ],
                ),
            )
        )

        return int(
            self.db.scalar(
                statement,
            )
            or 0,
        )

    def count_extracted_features(
        self,
    ) -> int:
        """
        Count successfully extracted feature records.
        """

        return self.count_feature_status(
            FeatureExtractionStatus.EXTRACTED,
        )

    def count_warning_features(
        self,
    ) -> int:
        """
        Count feature records extracted with warnings.
        """

        return self.count_feature_status(
            FeatureExtractionStatus.WARNING,
        )

    def count_failed_features(
        self,
    ) -> int:
        """
        Count failed feature extraction records.
        """

        return self.count_feature_status(
            FeatureExtractionStatus.FAILED,
        )

    # ========================================================
    # PENDING FEATURES
    # ========================================================

    def count_pending_features(
        self,
    ) -> int:
        """
        Count parsed emails without an EmailFeatures record.

        Canonical formula:

            pending =
                parsed emails
                -
                parsed emails with feature records

        SQL:

            ParsedEmail
                LEFT JOIN EmailFeatures
                WHERE EmailFeatures.id IS NULL
        """

        statement = (
            select(
                func.count(
                    ParsedEmail.id,
                ),
            )
            .select_from(
                ParsedEmail,
            )
            .outerjoin(
                EmailFeatures,
                EmailFeatures.email_id
                == ParsedEmail.email_id,
            )
            .where(
                EmailFeatures.id.is_(None),
                ParsedEmail.status.in_(
                    [
                        SourceParsingStatus.PARSED,
                        SourceParsingStatus.WARNING,
                    ],
                ),
            )
        )

        return int(
            self.db.scalar(
                statement,
            )
            or 0,
        )

    # ========================================================
    # SUMMARY
    # ========================================================

    def get_summary_counts(
        self,
    ) -> dict[str, int]:
        """
        Return canonical Module 04 summary counters.

        Counters:

            total_collected
            total_parsed
            total_features_ready
            total_pending
            total_warnings
            total_failed
        """

        total_collected = (
            self.count_emails()
        )

        total_parsed = (
            self.count_parsed_emails()
        )

        total_features_ready = (
            self.count_extracted_features()
        )

        total_pending = (
            self.count_pending_features()
        )

        total_warnings = (
            self.count_warning_features()
        )

        total_failed = (
            self.count_failed_features()
        )

        return {
            "total_collected": total_collected,
            "total_parsed": total_parsed,
            "total_features_ready": total_features_ready,
            "total_pending": total_pending,
            "total_warnings": total_warnings,
            "total_failed": total_failed,
        }

    # ========================================================
    # EXTRACTION ELIGIBILITY
    # ========================================================

    def should_extract(
        self,
        email_id: UUID,
        *,
        force: bool = False,
    ) -> bool:
        """
        Determine whether feature extraction should execute.

        Rules:

            force=True
                -> True

            No feature record
                -> True

            EXTRACTED
                -> False

            WARNING
                -> False

            FAILED
                -> True
        """

        if force:
            return True

        feature = self.get_feature(
            email_id,
        )

        if feature is None:
            return True

        return (
            feature.status
            == FeatureExtractionStatus.FAILED
        )

    # ========================================================
    # FAILED EXTRACTION STATE
    # ========================================================

    def mark_feature_failed(
        self,
        email_id: UUID,
        *,
        error_message: str,
        extractor_version: str,
        processing_time_ms: int = 0,
        extracted_at: datetime | None = None,
    ) -> EmailFeatures:
        """
        Persist a failed feature extraction state.

        If no feature row exists:

            create FAILED feature record

        If a feature row exists:

            update its extraction state to FAILED

        Source email and parsed email remain untouched.
        """

        timestamp = (
            extracted_at
            if extracted_at is not None
            else datetime.now(
                timezone.utc,
            )
        )

        normalized_processing_time = max(
            0,
            processing_time_ms,
        )

        existing = self.get_feature(
            email_id,
        )

        # ----------------------------------------------------
        # CREATE FAILED RECORD
        # ----------------------------------------------------

        if existing is None:
            feature = EmailFeatures(
                email_id=email_id,

                # F1-F8
                f1_sender_email=None,
                f2_known_domain=False,
                f3_message_id=False,
                f4_auto_submitted=False,
                f5_precedence_bulk=False,
                f6_list_id=False,
                f7_x_beenthere=False,
                f8_x_anti_abuse=False,

                # F9-F12
                f9_keyword_features=0,
                f10_subject_length=0,
                f11_emails_per_minute=0,
                f12_emails_per_hour=0,

                # Empty vector because extraction failed
                feature_vector={},

                validation_errors=[
                    error_message,
                ],

                validation_warnings=[],

                status=(
                    FeatureExtractionStatus.FAILED
                ),

                extractor_version=(
                    extractor_version
                ),

                processing_time_ms=(
                    normalized_processing_time
                ),

                extracted_at=timestamp,

                created_at=timestamp,

                updated_at=timestamp,
            )

            self.db.add(
                feature,
            )

            self.db.flush()

            return feature

        # ----------------------------------------------------
        # UPDATE FAILED RECORD
        # ----------------------------------------------------

        existing.validation_errors = [
            error_message,
        ]

        existing.validation_warnings = []

        existing.status = (
            FeatureExtractionStatus.FAILED
        )

        existing.extractor_version = (
            extractor_version
        )

        existing.processing_time_ms = (
            normalized_processing_time
        )

        existing.extracted_at = timestamp

        existing.updated_at = (
            datetime.now(
                timezone.utc,
            )
        )

        self.db.flush()

        return existing
