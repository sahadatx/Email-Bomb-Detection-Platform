from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable, Sequence
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.features.definitions import FEATURE_COUNT
from app.modules.features.extractor import (
    EXTRACTOR_VERSION,
    ParsedEmailInput,
    extract_features,
)
from app.modules.features.models import (
    EmailFeatures,
    FeatureExtractionStatus,
)
from app.modules.features.repository import (
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    FeatureRepository,
)
from app.modules.features.schemas import (
    FeatureWorkspaceFilters,
)
from app.modules.parsing.models import (
    ParsedEmail,
    ParsingStatus as SourceParsingStatus,
)


# ============================================================
# EXCEPTIONS
# ============================================================


class FeatureServiceError(Exception):
    """
    Base exception for Module 04 business workflow errors.
    """


class EmailNotFoundError(FeatureServiceError):
    """
    Raised when the canonical Module 02 email does not exist.
    """


class ParsedEmailNotFoundError(FeatureServiceError):
    """
    Raised when the email has not been successfully parsed
    by Module 03.
    """


class FeatureExtractionError(FeatureServiceError):
    """
    Raised when F1-F12 feature extraction fails.
    """


# ============================================================
# SERVICE
# ============================================================


class FeatureService:
    """
    Business workflow layer for Module 04 — Feature Engineering.

    Responsibilities
    ----------------
    - Coordinate repository and extractor
    - Validate extraction prerequisites
    - Build ParsedEmailInput
    - Execute F1-F12 extraction
    - Persist extraction results
    - Handle failed extraction states
    - Handle re-extraction
    - Provide filtered Feature Workspace data
    - Provide complete filtered selection data
    - Provide Feature Engineering summary
    - Provide extraction eligibility
    - Provide module metadata

    Module Boundary
    ---------------
    Module 04 consumes successfully parsed emails from Module 03.

        Module 02
            Collected Emails
                ↓
        Module 03
            Parsed Emails
                ↓
        Module 04
            F1-F12 Feature Engineering

    Module 04 does not perform:

        - email ingestion
        - MIME parsing
        - email normalization
        - ML
        - classification
        - prediction
        - confidence scoring
        - risk scoring
        - threat scoring

    Workspace Filtering
    -------------------
    Supported filters:

        - Search
        - Source
        - Level
        - Status
        - From date
        - To date

    Filter semantics:

        AND

    Pagination
    ----------
    Pagination controls only the displayed workspace rows.

    It does NOT control global selection.

    Global Selection
    ----------------
    "Select All Matching" resolves the complete filtered
    selectable population through the repository.

    Example:

        page_size = 30
        filtered_total = 347
        selectable_total = 312

    The service returns all 312 selectable IDs.

    It does not restrict selection to the current 30-row page.
    """

    def __init__(
        self,
        db: Session,
        repository: FeatureRepository | None = None,
    ) -> None:
        self.db = db

        self.repository = (
            repository
            if repository is not None
            else FeatureRepository(db)
        )

    # ========================================================
    # INTERNAL LOOKUPS
    # ========================================================

    def _get_email_or_raise(
        self,
        email_id: UUID,
    ):
        """
        Return the canonical Module 02 email.

        Raises:
            EmailNotFoundError
        """

        email = self.repository.get_email(
            email_id,
        )

        if email is None:
            raise EmailNotFoundError(
                f"Email {email_id} was not found.",
            )

        return email

    def _get_parsed_email_or_raise(
        self,
        email_id: UUID,
    ) -> ParsedEmail:
        """
        Return the Module 03 parsed representation.

        Raises:
            ParsedEmailNotFoundError
        """

        parsed_email = (
            self.repository.get_parsed_email(
                email_id,
            )
        )

        if parsed_email is None:
            raise ParsedEmailNotFoundError(
                f"Email {email_id} has not been parsed yet.",
            )

        parsing_status = getattr(
            parsed_email.status,
            "value",
            parsed_email.status,
        )
        if parsing_status == SourceParsingStatus.FAILED.value:
            raise ParsedEmailNotFoundError(
                f"Email {email_id} did not pass parsing and cannot be used for feature extraction.",
            )

        return parsed_email

    # ========================================================
    # PARSED EMAIL FIELD ACCESS
    # ========================================================

    @staticmethod
    def _get_parsed_value(
        parsed_email: ParsedEmail,
        *names: str,
        default: Any = None,
    ) -> Any:
        """
        Return the first available ParsedEmail attribute.

        Module 03 remains the source of parsed header/body
        information.

        Module 02 remains the source of canonical email
        identity and timestamps.
        """

        for name in names:
            if not hasattr(
                parsed_email,
                name,
            ):
                continue

            value = getattr(
                parsed_email,
                name,
            )

            if value is not None:
                return value

        return default

    @staticmethod
    def _get_parsed_header_value(
        parsed_email: ParsedEmail,
        *names: str,
    ) -> str | None:
        """Read one or more normalized headers from Module 03 storage."""
        headers = getattr(parsed_email, "headers", None) or {}
        if not isinstance(headers, dict):
            return None

        wanted = {name.strip().lower() for name in names}
        values: list[str] = []
        for name, raw_values in headers.items():
            if str(name).strip().lower() not in wanted:
                continue
            candidates = raw_values if isinstance(raw_values, list) else [raw_values]
            values.extend(
                str(value).strip()
                for value in candidates
                if value is not None and str(value).strip()
            )

        return ", ".join(values) or None

    # ========================================================
    # EXTRACTOR INPUT
    # ========================================================

    def _build_extractor_input(
        self,
        email_id: UUID,
    ) -> ParsedEmailInput:
        """
        Build the canonical ParsedEmailInput consumed by the
        F1-F12 extractor.

        Source ownership
        ----------------

        Module 02 Email:
            - sender
            - subject
            - message_id fallback
            - received_at

        Module 03 ParsedEmail:
            - parsed headers
            - normalized text body

        Repository:
            - complete collected received_at population
              required by F11/F12
        """

        email = self._get_email_or_raise(
            email_id,
        )

        parsed = self._get_parsed_email_or_raise(
            email_id,
        )

        # ----------------------------------------------------
        # Header values
        # ----------------------------------------------------

        message_id = self._get_parsed_value(
            parsed,
            "message_id",
            default=email.message_id,
        )

        auto_submitted = self._get_parsed_header_value(
            parsed,
            "auto-submitted",
        )

        precedence = self._get_parsed_header_value(
            parsed,
            "precedence",
        )

        list_id = self._get_parsed_header_value(
            parsed,
            "list_id",
            "list-id",
        )

        x_beenthere = self._get_parsed_header_value(
            parsed,
            "x_beenthere",
            "x_been_there",
            "x-beenthere",
            "x-been-there",
        )

        x_anti_abuse = self._get_parsed_header_value(
            parsed,
            "x_anti_abuse",
            "x_antiabuse",
            "x-anti-abuse",
            "x-antiabuse",
        )

        # ----------------------------------------------------
        # Normalized text body
        # ----------------------------------------------------

        text_body = self._get_parsed_value(
            parsed,
            "text_body",
            "body_text",
            "plain_text",
            default="",
        )

        # ----------------------------------------------------
        # Complete temporal population
        #
        # F11/F12 must use all collected emails.
        #
        # Never use:
        #   - current workspace page
        #   - workspace filters
        #   - selected batch only
        # ----------------------------------------------------

        received_at_values = (
            self.repository.get_received_at_values()
        )

        return ParsedEmailInput(
            sender=email.sender,
            subject=email.subject,
            message_id=message_id,
            auto_submitted=auto_submitted,
            precedence=precedence,
            list_id=list_id,
            x_beenthere=x_beenthere,
            x_anti_abuse=x_anti_abuse,
            text_body=text_body,
            received_at=email.received_at,
            all_received_at=received_at_values,
        )

    # ========================================================
    # VECTOR → DATABASE COLUMN MAPPING
    # ========================================================

    @staticmethod
    def _vector_to_columns(
        vector: dict[str, object],
    ) -> dict[str, object]:
        """
        Convert canonical F1-F12 vector keys into the
        EmailFeatures database column representation.
        """

        return {
            "f1_sender_email": vector.get(
                "F1",
            ),

            "f2_known_domain": bool(
                vector.get(
                    "F2",
                    False,
                ),
            ),

            "f3_message_id": bool(
                vector.get(
                    "F3",
                    False,
                ),
            ),

            "f4_auto_submitted": bool(
                vector.get(
                    "F4",
                    False,
                ),
            ),

            "f5_precedence_bulk": bool(
                vector.get(
                    "F5",
                    False,
                ),
            ),

            "f6_list_id": bool(
                vector.get(
                    "F6",
                    False,
                ),
            ),

            "f7_x_beenthere": bool(
                vector.get(
                    "F7",
                    False,
                ),
            ),

            "f8_x_anti_abuse": bool(
                vector.get(
                    "F8",
                    False,
                ),
            ),

            "f9_keyword_features": max(
                0,
                int(
                    vector.get(
                        "F9",
                        0,
                    )
                    or 0
                ),
            ),

            "f10_subject_length": max(
                0,
                int(
                    vector.get(
                        "F10",
                        0,
                    )
                    or 0
                ),
            ),

            "f11_emails_per_minute": max(
                0,
                int(
                    vector.get(
                        "F11",
                        0,
                    )
                    or 0
                ),
            ),

            "f12_emails_per_hour": max(
                0,
                int(
                    vector.get(
                        "F12",
                        0,
                    )
                    or 0
                ),
            ),
        }

    # ========================================================
    # SINGLE EMAIL EXTRACTION
    # ========================================================

    def extract_features(
        self,
        email_id: UUID,
        *,
        force: bool = False,
        trusted_domains: Iterable[str] | None = None,
    ) -> EmailFeatures:
        """
        Execute the complete F1-F12 extraction workflow.

        Workflow:

            Canonical Email
                ↓
            Parsed Email
                ↓
            Extraction Eligibility
                ↓
            ParsedEmailInput
                ↓
            F1-F12 Extractor
                ↓
            Validation
                ↓
            EmailFeatures Upsert
        """

        # ----------------------------------------------------
        # 1. Canonical email validation
        # ----------------------------------------------------

        self._get_email_or_raise(
            email_id,
        )

        # ----------------------------------------------------
        # 2. Parsed email validation
        # ----------------------------------------------------

        self._get_parsed_email_or_raise(
            email_id,
        )

        # ----------------------------------------------------
        # 3. Extraction eligibility
        # ----------------------------------------------------

        if not self.repository.should_extract(
            email_id,
            force=force,
        ):
            existing = (
                self.repository.get_feature(
                    email_id,
                )
            )

            if existing is None:
                raise FeatureExtractionError(
                    "Feature extraction was skipped, "
                    "but no feature record exists.",
                )

            return existing

        # ----------------------------------------------------
        # 4. Build extractor input
        # ----------------------------------------------------

        extractor_input = (
            self._build_extractor_input(
                email_id,
            )
        )

        extracted_at = datetime.now(
            timezone.utc,
        )

        # ----------------------------------------------------
        # 5. Execute F1-F12
        # ----------------------------------------------------

        try:
            result = extract_features(
                email=extractor_input,
                trusted_domains=trusted_domains,
            )

        except Exception as exc:
            try:
                self.repository.mark_feature_failed(
                    email_id,
                    error_message=str(
                        exc,
                    ),
                    extractor_version=(
                        EXTRACTOR_VERSION
                    ),
                    processing_time_ms=0,
                    extracted_at=extracted_at,
                )
            except Exception:
                # Preserve the original extractor exception.
                pass

            raise FeatureExtractionError(
                f"Feature extraction failed for "
                f"email {email_id}: {exc}",
            ) from exc

        # ----------------------------------------------------
        # 6. Extractor-reported validation errors
        # ----------------------------------------------------

        if result.errors:
            error_message = "; ".join(
                str(error)
                for error in result.errors
            )

            try:
                self.repository.mark_feature_failed(
                    email_id,
                    error_message=error_message,
                    extractor_version=(
                        result.extractor_version
                    ),
                    processing_time_ms=(
                        result.processing_time_ms
                    ),
                    extracted_at=extracted_at,
                )
            except Exception:
                pass

            raise FeatureExtractionError(
                error_message,
            )

        # ----------------------------------------------------
        # 7. Determine persisted extraction status
        # ----------------------------------------------------

        extraction_status = (
            FeatureExtractionStatus.WARNING
            if result.warnings
            else FeatureExtractionStatus.EXTRACTED
        )

        # ----------------------------------------------------
        # 8. Validate vector shape
        # ----------------------------------------------------

        feature_vector = dict(
            result.feature_vector,
        )

        expected_feature_ids = {
            f"F{index}"
            for index in range(
                1,
                FEATURE_COUNT + 1,
            )
        }

        actual_feature_ids = set(
            feature_vector.keys(),
        )

        missing_features = (
            expected_feature_ids
            - actual_feature_ids
        )

        if missing_features:
            error_message = (
                "Feature extraction returned an incomplete "
                "feature vector. Missing: "
                + ", ".join(
                    sorted(
                        missing_features,
                    ),
                )
            )

            try:
                self.repository.mark_feature_failed(
                    email_id,
                    error_message=error_message,
                    extractor_version=(
                        result.extractor_version
                    ),
                    processing_time_ms=(
                        result.processing_time_ms
                    ),
                    extracted_at=extracted_at,
                )
            except Exception:
                pass

            raise FeatureExtractionError(
                error_message,
            )

        # ----------------------------------------------------
        # 9. Map vector → database columns
        # ----------------------------------------------------

        columns = self._vector_to_columns(
            feature_vector,
        )

        # ----------------------------------------------------
        # 10. Persist extraction
        # ----------------------------------------------------

        try:
            return self.repository.upsert_features(
                email_id,
                **columns,
                feature_vector=feature_vector,
                validation_errors=list(
                    result.errors,
                ),
                validation_warnings=list(
                    result.warnings,
                ),
                status=extraction_status,
                extractor_version=(
                    result.extractor_version
                ),
                processing_time_ms=(
                    result.processing_time_ms
                ),
                extracted_at=extracted_at,
            )

        except Exception as exc:
            self.db.rollback()

            failure_message = (
                "Feature persistence failed: "
                f"{exc}"
            )

            try:
                self.repository.mark_feature_failed(
                    email_id,
                    error_message=failure_message,
                    extractor_version=(
                        result.extractor_version
                        or EXTRACTOR_VERSION
                    ),
                    processing_time_ms=(
                        result.processing_time_ms
                    ),
                    extracted_at=extracted_at,
                )
            except Exception:
                # Preserve the original persistence error.
                pass

            raise FeatureExtractionError(
                f"Feature persistence failed for "
                f"email {email_id}: {exc}",
            ) from exc

    # ========================================================
    # BATCH EXTRACTION
    # ========================================================

    def extract_features_batch(
        self,
        email_ids: Sequence[UUID],
        *,
        force: bool = False,
        trusted_domains: Iterable[str] | None = None,
    ) -> list[EmailFeatures]:
        """
        Extract features for multiple email IDs.

        Processing behavior
        -------------------
        - Duplicate IDs are removed.
        - Caller order is preserved.
        - Each email is processed independently.
        - One failure does not stop remaining emails.
        - Successfully processed feature records are returned.

        Large selections can be supplied by the caller.
        The repository and extraction workflow remain
        independent from UI pagination.
        """

        if not email_ids:
            return []

        # ----------------------------------------------------
        # Deduplicate while preserving order
        # ----------------------------------------------------

        unique_ids: list[UUID] = []
        seen: set[UUID] = set()

        for email_id in email_ids:
            if email_id in seen:
                continue

            seen.add(email_id)
            unique_ids.append(
                email_id,
            )

        results: list[EmailFeatures] = []

        for email_id in unique_ids:
            try:
                feature = self.extract_features(
                    email_id,
                    force=force,
                    trusted_domains=trusted_domains,
                )
            except FeatureServiceError:
                continue

            results.append(
                feature,
            )

        return results

    # ========================================================
    # RE-EXTRACTION
    # ========================================================

    def reextract_features(
        self,
        email_id: UUID,
        *,
        trusted_domains: Iterable[str] | None = None,
    ) -> EmailFeatures:
        """
        Force re-extraction of F1-F12.

        Existing EmailFeatures data is updated through the
        repository upsert operation.

        No duplicate feature row is created.
        """

        return self.extract_features(
            email_id,
            force=True,
            trusted_domains=trusted_domains,
        )

    # ========================================================
    # FEATURE LOOKUP
    # ========================================================

    def get_feature(
        self,
        email_id: UUID,
    ) -> EmailFeatures:
        """
        Return persisted feature data for one email.

        Raises:

            EmailNotFoundError
                Canonical email does not exist.

            FeatureExtractionError
                Email exists but no feature record exists.
        """

        self._get_email_or_raise(
            email_id,
        )

        feature = self.repository.get_feature(
            email_id,
        )

        if feature is None:
            raise FeatureExtractionError(
                f"Features are not available for "
                f"email {email_id}.",
            )

        return feature

    # ========================================================
    # FEATURE WORKSPACE
    # ========================================================

    def get_workspace(
        self,
        *,
        page: int = DEFAULT_PAGE,
        page_size: int = DEFAULT_PAGE_SIZE,
        filters: FeatureWorkspaceFilters | None = None,
    ) -> tuple[
        list[
            tuple[
                Any,
                ParsedEmail,
                EmailFeatures | None,
            ]
        ],
        int,
    ]:
        """
        Return the filtered, paginated Feature Workspace.

        Pagination controls displayed rows only.

        The returned total is the complete filtered result
        count, not the current page count.

        Supported filters:

            Search
            Source
            Level
            Status
            From date
            To date

        All filters use AND semantics.
        """

        normalized_page = max(
            DEFAULT_PAGE,
            int(page),
        )

        normalized_page_size = min(
            max(
                1,
                int(page_size),
            ),
            MAX_PAGE_SIZE,
        )

        return self.repository.list_feature_page(
            page=normalized_page,
            page_size=normalized_page_size,
            filters=filters,
        )

    # ========================================================
    # FEATURE WORKSPACE COUNT
    # ========================================================

    def count_workspace(
        self,
        *,
        filters: FeatureWorkspaceFilters | None = None,
    ) -> int:
        """
        Return the COMPLETE number of Feature Workspace rows
        matching the supplied filters.

        This is independent from pagination.
        """

        return self.repository.count_feature_workspace(
            filters=filters,
        )

    # ========================================================
    # GLOBAL SELECTABLE EMAIL IDS
    # ========================================================

    def get_selectable_email_ids(
        self,
        *,
        filters: FeatureWorkspaceFilters | None = None,
    ) -> list[UUID]:
        """
        Return ALL selectable email IDs matching the supplied
        Feature Workspace filters.

        This method powers:

            Select All Matching

        IMPORTANT
        ---------
        Pagination is intentionally ignored.

        Example:

            page_size = 30
            filtered workspace = 347
            selectable = 312

        returns all 312 selectable email IDs.

        Selectable states:

            pending
            warning
            failed

        Extracted records are excluded.

        Only successfully parsed emails participate.
        """

        return (
            self.repository
            .list_selectable_feature_email_ids(
                filters=filters,
            )
        )

    # ========================================================
    # GLOBAL SELECTABLE COUNT
    # ========================================================

    def count_selectable_emails(
        self,
        *,
        filters: FeatureWorkspaceFilters | None = None,
    ) -> int:
        """
        Return the COMPLETE selectable count for the supplied
        Feature Workspace filters.

        This is independent from pagination.

        Example:

            filtered_total = 347
            selectable_total = 312

        returns:

            312
        """

        return (
            self.repository
            .count_selectable_feature_emails(
                filters=filters,
            )
        )

    # ========================================================
    # GLOBAL SELECTION
    # ========================================================

    def get_selection_summary(
        self,
        *,
        filters: FeatureWorkspaceFilters | None = None,
    ) -> dict[str, int]:
        """
        Return the complete filtered selection summary.

        Values:

            matching
                Total parsed emails matching filters.

            selectable
                Total matching emails that can be extracted.

        Example:

            {
                "matching": 347,
                "selectable": 312,
            }

        This is intentionally independent from UI pagination.
        """

        matching = self.count_workspace(
            filters=filters,
        )

        selectable = self.count_selectable_emails(
            filters=filters,
        )

        return {
            "matching": matching,
            "selectable": selectable,
        }

    # ========================================================
    # SUMMARY
    # ========================================================

    def get_summary(
        self,
    ) -> dict[str, float | int]:
        """
        Return the global Module 04 summary.

        Readiness is based on successfully parsed emails.

        Formula:

            readiness_percentage =
                total_features_ready
                --------------------
                total_parsed
                × 100

        If no emails are parsed:

            readiness_percentage = 0.0
        """

        counts = (
            self.repository.get_summary_counts()
        )

        total_parsed = int(
            counts[
                "total_parsed"
            ],
        )

        total_features_ready = int(
            counts[
                "total_features_ready"
            ],
        )

        if total_parsed <= 0:
            readiness_percentage = 0.0

        else:
            readiness_percentage = round(
                (
                    total_features_ready
                    / total_parsed
                )
                * 100.0,
                2,
            )

        return {
            **counts,
            "readiness_percentage": (
                readiness_percentage
            ),
        }

    # ========================================================
    # EXTRACTION ELIGIBILITY
    # ========================================================

    def can_extract(
        self,
        email_id: UUID,
    ) -> bool:
        """
        Determine whether an email satisfies Module 04
        extraction prerequisites.

        Requirements:

            canonical Email exists
            AND
            ParsedEmail exists
        """

        if not self.repository.email_exists(
            email_id,
        ):
            return False

        return self.repository.parsed_email_exists(
            email_id,
        )

    # ========================================================
    # DELETE / RESET
    # ========================================================

    def delete_features(
        self,
        email_id: UUID,
    ) -> bool:
        """
        Delete only the Module 04 feature record.

        Module 02 email data and Module 03 parsed data remain
        untouched.
        """

        self._get_email_or_raise(
            email_id,
        )

        return self.repository.delete_features(
            email_id,
        )

    # ========================================================
    # MODULE METADATA
    # ========================================================

    def get_module_metadata(
        self,
    ) -> dict[str, object]:
        """
        Return static Module 04 metadata.
        """

        return {
            "module": "feature-engineering",
            "feature_schema": "F1-F12",
            "feature_count": FEATURE_COUNT,
            "extractor_version": EXTRACTOR_VERSION,
        }
