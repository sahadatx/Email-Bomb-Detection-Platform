from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import UUID

from app.modules.emails.models import (
    Email,
    EmailGroundTruthLabel,
    EmailSource,
)
from app.modules.emails.repository import EmailRepository

from .models import ParsedEmail as ParsedEmailModel
from .models import ParsingStatus as ParsingStatusModel
from .parser import EmailParser, ParsedEmail
from .repository import ParsingRepository
from .schemas import (
    ParsedAttachment,
    ParsedEmailIdentity,
    ParsedEmailResponse,
    ParsedEmailTimestamps,
    ParsedMimePart,
    ParsingEmailListItem,
    ParsingMetadata,
    ParsingPersistenceSummary,
    ParsingStatus,
)


# ============================================================
# CONSTANTS
# ============================================================

DEFAULT_PAGE_SIZE = 30
MAX_PAGE_SIZE = 100


# ============================================================
# EXCEPTIONS
# ============================================================


class ParsingEmailNotFoundError(Exception):
    """
    Raised when a requested collected email or parsed result
    does not exist.
    """


# ============================================================
# SERVICE
# ============================================================


class ParsingService:
    """
    Application service for Module 03 — Email Parsing.

    Module 02 remains the canonical source for collected emails.

    Processing flow:

        Module 02 EmailRepository
                    ↓
              Raw Email
                    ↓
              EmailParser
                    ↓
             Normalization
                    ↓
               Validation
                    ↓
          ParsedEmail model
                    ↓
          ParsingRepository
                    ↓
            API response

    Parsing Workspace flow:

        Module 02 Email
              +
        Module 03 ParsedEmail
              ↓
        LEFT JOIN workspace
              ↓
        Search / Filters / Pagination
              ↓
        Parsing Workspace

    Important architectural rules:

        1. Module 03 never deletes the original collected email.
        2. Module 02 owns source, level, received_at and raw data.
        3. Module 03 owns parsing status and parsed content.
        4. One collected email has at most one current parsed result.
        5. Re-parsing uses repository upsert.
        6. Pending means no ParsedEmail row exists.
        7. Pagination is independent of parsing batch size.
        8. Module 03 does not perform ML classification,
           risk scoring, confidence scoring, or threat scoring.
    """

    def __init__(
        self,
        email_repository: EmailRepository,
        parsing_repository: ParsingRepository,
        parser: EmailParser | None = None,
    ) -> None:
        self.email_repository = email_repository
        self.parsing_repository = parsing_repository
        self.parser = parser or EmailParser()

    # ========================================================
    # RETRIEVAL
    # ========================================================

    def get_email(
        self,
        email_id: UUID,
    ) -> Email:
        """
        Retrieve the canonical collected email from Module 02.
        """

        email = self.email_repository.get_by_id(
            email_id,
        )

        if email is None:
            raise ParsingEmailNotFoundError(
                f"Email '{email_id}' was not found."
            )

        return email

    # ========================================================
    # GLOBAL PARSING SUMMARY
    # ========================================================

    def get_parsing_summary(
        self,
    ) -> ParsingPersistenceSummary:
        """
        Return the complete global parsing state.

        This is independent of workspace filters and pagination.

        Only successfully parsed emails are considered ready
        for Module 04 Feature Engineering.
        """

        counts = (
            self.parsing_repository.get_summary_counts()
        )

        total_collected = int(
            counts["total_collected"],
        )

        total_parsed = int(
            counts["parsed"],
        )

        total_pending = int(
            counts["pending"],
        )

        total_warnings = int(
            counts["warnings"],
        )

        total_failed = int(
            counts["failed"],
        )

        # ----------------------------------------------------
        # Module 04 readiness
        # ----------------------------------------------------

        ready_for_features = total_parsed

        if total_collected > 0:
            readiness_percentage = round(
                (
                    ready_for_features
                    / total_collected
                )
                * 100,
                2,
            )
        else:
            readiness_percentage = 0.0

        return ParsingPersistenceSummary(
            total_collected=total_collected,
            total_parsed=total_parsed,
            total_pending=total_pending,
            total_warnings=total_warnings,
            total_failed=total_failed,
            ready_for_features=ready_for_features,
            readiness_percentage=readiness_percentage,
        )

    # ========================================================
    # LIST PARSING WORKSPACE
    # ========================================================

    def list_emails(
        self,
        *,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
        search: str | None = None,
        source: EmailSource | None = None,
        level: EmailGroundTruthLabel | None = None,
        status: ParsingStatus | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> tuple[list[ParsingEmailListItem], int]:
        """
        Return the paginated Parsing Workspace.

        Final table:

            Subject
            Sender
            Source
            Level
            Received
            Status
            Action

        Important:

            Source
                -> Module 02

            Level
                -> Module 02 ground_truth_label

            Received
                -> Module 02 received_at

            Status
                -> Module 03 ParsingStatus

        Pending emails are included because the repository uses
        Email LEFT OUTER JOIN ParsedEmail.
        """

        page = max(
            1,
            int(page),
        )

        page_size = min(
            MAX_PAGE_SIZE,
            max(
                1,
                int(page_size),
            ),
        )

        rows, total = (
            self.parsing_repository.list_workspace(
                page=page,
                page_size=page_size,
                search=search,
                source=source,
                level=level,
                status=status,
                from_date=from_date,
                to_date=to_date,
            )
        )

        items = [
            self._to_workspace_list_item(
                email=email,
                parsed=persisted,
            )
            for email, persisted in rows
        ]

        return (
            items,
            total,
        )

    # ========================================================
    # BULK MATCHING
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
        Return every email ID matching the active workspace
        filters.

        This is intentionally not paginated.

        Used for:

            Select All Matching
            Parse All Matching
        """

        return (
            self.parsing_repository.get_matching_email_ids(
                search=search,
                source=source,
                level=level,
                status=status,
                from_date=from_date,
                to_date=to_date,
            )
        )

    # ========================================================
    # PENDING EMAIL IDS
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
        Return all pending email IDs matching the optional
        workspace filters.

        Pending means:

            Module 02 Email exists
            AND
            Module 03 ParsedEmail does not exist
        """

        return (
            self.parsing_repository.get_pending_email_ids(
                search=search,
                source=source,
                level=level,
                from_date=from_date,
                to_date=to_date,
            )
        )

    # ========================================================
    # PARSE ONE
    # ========================================================

    def parse_email(
        self,
        email_id: UUID,
    ) -> ParsedEmailResponse:
        """
        Parse one collected email and persist its parsed result.
        """

        # ----------------------------------------------------
        # 1. Load canonical Module 02 email.
        # ----------------------------------------------------

        email = self.get_email(
            email_id,
        )

        # ----------------------------------------------------
        # 2. Parse original raw MIME content.
        # ----------------------------------------------------

        parsed = self.parser.parse(
            email.raw_content,
        )

        # ----------------------------------------------------
        # 3. Determine Module 03 parsing status.
        # ----------------------------------------------------

        parsing_status = (
            self._get_parsing_status(
                parsed,
            )
        )

        # ----------------------------------------------------
        # 4. Build persistence model.
        # ----------------------------------------------------

        parsed_model = (
            self._build_parsed_email_model(
                email=email,
                parsed=parsed,
                parsing_status=parsing_status,
            )
        )

        # ----------------------------------------------------
        # 5. Persist through upsert.
        # ----------------------------------------------------

        persisted = (
            self.parsing_repository.upsert(
                parsed_model,
            )
        )

        # ----------------------------------------------------
        # 6. Return complete parsed response.
        # ----------------------------------------------------

        return self._build_parsing_response(
            email=email,
            parsed=parsed,
            persisted=persisted,
        )

    # ========================================================
    # PARSE MULTIPLE
    # ========================================================

    def parse_emails(
        self,
        email_ids: list[UUID],
    ) -> list[ParsedEmailResponse]:
        """
        Parse multiple collected emails.

        Each email is processed independently.

        Re-parsing updates the existing parsed result.
        """

        results: list[ParsedEmailResponse] = []

        for email_id in email_ids:
            results.append(
                self.parse_email(
                    email_id,
                )
            )

        return results

    # ========================================================
    # PARSE MATCHING
    # ========================================================

    def parse_matching_emails(
        self,
        *,
        search: str | None = None,
        source: EmailSource | None = None,
        level: EmailGroundTruthLabel | None = None,
        status: ParsingStatus | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[ParsedEmailResponse]:
        """
        Parse every email matching the supplied filters.

        Pagination is intentionally ignored.

        The repository first resolves all matching source email
        IDs, then parsing is performed one email at a time.

        Large-scale background job orchestration can later wrap
        this service operation without changing the core parser.
        """

        email_ids = (
            self.parsing_repository.get_matching_email_ids(
                search=search,
                source=source,
                level=level,
                status=status,
                from_date=from_date,
                to_date=to_date,
            )
        )

        return self.parse_emails(
            email_ids,
        )

    # ========================================================
    # PARSE ALL PENDING
    # ========================================================

    def parse_all_pending(
        self,
        *,
        search: str | None = None,
        source: EmailSource | None = None,
        level: EmailGroundTruthLabel | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[ParsedEmailResponse]:
        """
        Parse all currently pending emails matching the optional
        workspace filters.

        Pagination is ignored.

        Pending emails are resolved by the repository using
        Email LEFT JOIN ParsedEmail semantics.
        """

        email_ids = (
            self.parsing_repository.get_pending_email_ids(
                search=search,
                source=source,
                level=level,
                from_date=from_date,
                to_date=to_date,
            )
        )

        return self.parse_emails(
            email_ids,
        )

    # ========================================================
    # API ALIASES
    # ========================================================

    def parse_and_validate_email(
        self,
        email_id: UUID,
    ) -> ParsedEmailResponse:
        """
        Public service entrypoint for single-email parsing.

        Validation is performed by EmailParser.
        """

        return self.parse_email(
            email_id,
        )

    def parse_and_validate_emails(
        self,
        email_ids: list[UUID],
    ) -> list[ParsedEmailResponse]:
        """
        Public service entrypoint for explicit batch parsing.
        """

        return self.parse_emails(
            email_ids,
        )

    # ========================================================
    # GET PERSISTED PARSED RESULT
    # ========================================================

    def get_parsed_email(
        self,
        email_id: UUID,
    ) -> ParsedEmailResponse:
        """
        Return the persisted parsed result for a collected email.

        This method does not execute the parser again.

        If no parsed result exists, the email is still pending.
        """

        email = self.get_email(
            email_id,
        )

        persisted = (
            self.parsing_repository.get_by_email_id(
                email_id,
            )
        )

        if persisted is None:
            raise ParsingEmailNotFoundError(
                f"Parsed result for email '{email_id}' "
                "was not found."
            )

        return self._build_persisted_response(
            email=email,
            persisted=persisted,
        )

    # ========================================================
    # LIST PERSISTED PARSED RESULTS
    # ========================================================

    def list_parsed_emails(
        self,
        *,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
        status: ParsingStatusModel | None = None,
    ) -> tuple[list[ParsedEmailModel], int]:
        """
        Return persisted parsed results only.

        This is separate from the main Parsing Workspace.

        The Parsing Workspace must use list_emails() because
        pending emails also need to be displayed.
        """

        page = max(
            1,
            int(page),
        )

        page_size = min(
            MAX_PAGE_SIZE,
            max(
                1,
                int(page_size),
            ),
        )

        return self.parsing_repository.list(
            page=page,
            page_size=page_size,
            status=status,
        )

    # ========================================================
    # BUILD DATABASE MODEL
    # ========================================================

    @staticmethod
    def _build_parsed_email_model(
        *,
        email: Email,
        parsed: ParsedEmail,
        parsing_status: ParsingStatus,
    ) -> ParsedEmailModel:
        """
        Convert the in-memory parser result into the persistent
        ParsedEmail SQLAlchemy model.
        """

        now = datetime.now(
            timezone.utc,
        )

        return ParsedEmailModel(
            email_id=email.id,

            message_id=parsed.message_id,

            subject=parsed.subject,

            sender=parsed.sender,

            recipients=list(
                parsed.recipients,
            ),

            reply_to=list(
                parsed.reply_to,
            ),

            cc=list(
                parsed.cc,
            ),

            bcc=list(
                parsed.bcc,
            ),

            date=parsed.date,

            headers=dict(
                parsed.headers,
            ),

            text_body=parsed.text_body,

            html_body=parsed.html_body,

            mime_parts=[
                {
                    "content_type": part.content_type,
                    "content_disposition": (
                        part.content_disposition
                    ),
                    "charset": part.charset,
                    "filename": part.filename,
                    "size": part.size,
                }
                for part in parsed.mime_parts
            ],

            attachments=[
                {
                    "filename": attachment.filename,
                    "content_type": (
                        attachment.content_type
                    ),
                    "content_disposition": (
                        attachment.content_disposition
                    ),
                    "size": attachment.size,
                    "content_id": attachment.content_id,
                }
                for attachment in parsed.attachments
            ],

            validation_errors=list(
                parsed.validation_errors,
            ),

            validation_warnings=list(
                parsed.validation_warnings,
            ),

            status=ParsingStatusModel(
                parsing_status.value,
            ),

            parser_version=parsed.parser_version,

            processing_time_ms=round(
                parsed.processing_time_ms,
            ),

            parsed_at=now,

            updated_at=now,
        )

    # ========================================================
    # PARSING STATUS
    # ========================================================

    @staticmethod
    def _get_parsing_status(
        parsed: ParsedEmail,
    ) -> ParsingStatus:
        """
        Convert parser validation results into Module 03
        parsing status.
        """

        if parsed.validation_errors:
            return ParsingStatus.FAILED

        if parsed.validation_warnings:
            return ParsingStatus.WARNING

        return ParsingStatus.PARSED

    # ========================================================
    # API RESPONSE — FRESH PARSE
    # ========================================================

    @staticmethod
    def _build_parsing_response(
        *,
        email: Email,
        parsed: ParsedEmail,
        persisted: ParsedEmailModel,
    ) -> ParsedEmailResponse:
        """
        Build the complete API response after parsing.

        Level is always taken from Module 02 ground truth.
        Parsing status is taken from Module 03.
        """

        parsing_status = ParsingStatus(
            persisted.status.value,
        )

        return ParsedEmailResponse(
            email_id=email.id,

            source=email.source,

            source_identifier=email.source_identifier,

            level=EmailGroundTruthLabel(
                email.ground_truth_label,
            ),

            identity=ParsedEmailIdentity(
                message_id=parsed.message_id,

                subject=parsed.subject,

                sender=parsed.sender,

                recipients=list(
                    parsed.recipients,
                ),

                reply_to=list(
                    parsed.reply_to,
                ),

                cc=list(
                    parsed.cc,
                ),

                bcc=list(
                    parsed.bcc,
                ),

                date=parsed.date,
            ),

            timestamps=ParsedEmailTimestamps(
                received_at=email.received_at,

                collected_at=email.collected_at,

                parsed_at=persisted.parsed_at,
            ),

            parsing=ParsingMetadata(
                status=parsing_status,

                parser_version=(
                    persisted.parser_version
                ),

                processing_time_ms=(
                    persisted.processing_time_ms
                ),
            ),

            headers=dict(
                parsed.headers,
            ),

            text_body=parsed.text_body,

            html_body=parsed.html_body,

            mime_parts=[
                ParsedMimePart(
                    content_type=part.content_type,
                    content_disposition=(
                        part.content_disposition
                    ),
                    charset=part.charset,
                    filename=part.filename,
                    size=part.size,
                )
                for part in parsed.mime_parts
            ],

            attachments=[
                ParsedAttachment(
                    filename=attachment.filename,
                    content_type=(
                        attachment.content_type
                    ),
                    content_disposition=(
                        attachment.content_disposition
                    ),
                    size=attachment.size,
                    content_id=attachment.content_id,
                )
                for attachment in parsed.attachments
            ],

            validation_errors=list(
                persisted.validation_errors or [],
            ),

            validation_warnings=list(
                persisted.validation_warnings or [],
            ),
        )

    # ========================================================
    # API RESPONSE — PERSISTED RESULT
    # ========================================================

    @staticmethod
    def _build_persisted_response(
        *,
        email: Email,
        persisted: ParsedEmailModel,
    ) -> ParsedEmailResponse:
        """
        Build an API response directly from the persisted
        parsed result.

        No re-parsing is performed.
        """

        parsing_status = ParsingStatus(
            persisted.status.value,
        )

        return ParsedEmailResponse(
            email_id=email.id,

            source=email.source,

            source_identifier=email.source_identifier,

            level=EmailGroundTruthLabel(
                email.ground_truth_label,
            ),

            identity=ParsedEmailIdentity(
                message_id=persisted.message_id,

                subject=persisted.subject,

                sender=persisted.sender,

                recipients=list(
                    persisted.recipients or [],
                ),

                reply_to=list(
                    persisted.reply_to or [],
                ),

                cc=list(
                    persisted.cc or [],
                ),

                bcc=list(
                    persisted.bcc or [],
                ),

                date=persisted.date,
            ),

            timestamps=ParsedEmailTimestamps(
                received_at=email.received_at,

                collected_at=email.collected_at,

                parsed_at=persisted.parsed_at,
            ),

            parsing=ParsingMetadata(
                status=parsing_status,

                parser_version=(
                    persisted.parser_version
                ),

                processing_time_ms=(
                    persisted.processing_time_ms
                ),
            ),

            headers=dict(
                persisted.headers or {},
            ),

            text_body=persisted.text_body,

            html_body=persisted.html_body,

            mime_parts=[
                ParsedMimePart(
                    content_type=part.get(
                        "content_type",
                        "application/octet-stream",
                    ),
                    content_disposition=part.get(
                        "content_disposition",
                    ),
                    charset=part.get(
                        "charset",
                    ),
                    filename=part.get(
                        "filename",
                    ),
                    size=part.get(
                        "size",
                        0,
                    ),
                )
                for part in (
                    persisted.mime_parts or []
                )
            ],

            attachments=[
                ParsedAttachment(
                    filename=attachment.get(
                        "filename",
                    ),
                    content_type=attachment.get(
                        "content_type",
                        "application/octet-stream",
                    ),
                    content_disposition=attachment.get(
                        "content_disposition",
                    ),
                    size=attachment.get(
                        "size",
                        0,
                    ),
                    content_id=attachment.get(
                        "content_id",
                    ),
                )
                for attachment in (
                    persisted.attachments or []
                )
            ],

            validation_errors=list(
                persisted.validation_errors or [],
            ),

            validation_warnings=list(
                persisted.validation_warnings or [],
            ),
        )

    # ========================================================
    # WORKSPACE LIST ITEM MAPPING
    # ========================================================

    @staticmethod
    def _to_workspace_list_item(
        *,
        email: Email,
        parsed: ParsedEmailModel | None,
    ) -> ParsingEmailListItem:
        """
        Convert one Email + optional ParsedEmail pair into the
        lightweight Parsing Workspace row.

        Final UI mapping:

            Subject
                -> parsed.subject when available,
                   otherwise Module 02 subject

            Sender
                -> parsed.sender when available,
                   otherwise Module 02 sender

            Source
                -> Module 02 email.source

            Level
                -> Module 02 email.ground_truth_label

            Received
                -> Module 02 email.received_at

            Status
                -> Module 03 parsed status
                   or PENDING when no parsed row exists
        """

        if parsed is None:
            parsing_status = ParsingStatus.PENDING

            message_id = email.message_id
            sender = email.sender
            subject = email.subject

        else:
            parsing_status = ParsingStatus(
                parsed.status.value,
            )

            message_id = (
                parsed.message_id
                or email.message_id
            )

            sender = (
                parsed.sender
                or email.sender
            )

            subject = (
                parsed.subject
                or email.subject
            )

        return ParsingEmailListItem(
            email_id=email.id,

            source=email.source,

            source_identifier=email.source_identifier,

            level=EmailGroundTruthLabel(
                email.ground_truth_label,
            ),

            message_id=message_id,

            sender=sender,

            subject=subject,

            received_at=email.received_at,

            collected_at=email.collected_at,

            parsing_status=parsing_status,
        )