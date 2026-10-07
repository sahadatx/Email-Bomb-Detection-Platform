from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)

from app.common.dependencies import database_session
from app.core.permissions import Permission
from app.core.rbac import require_permission
from app.modules.emails.models import (
    EmailGroundTruthLabel,
    EmailSource,
)
from app.modules.emails.repository import EmailRepository

from .models import ParsingStatus
from .repository import ParsingRepository
from .schemas import (
    ParseAllPendingRequest,
    ParseEmailRequest,
    ParseEmailsRequest,
    ParseMatchingEmailsRequest,
    ParsedEmailResponse,
    ParsingEmailListResponse,
    ParsingPersistenceSummary,
    ParsingStatus as ParsingStatusSchema,
)
from .service import (
    ParsingEmailNotFoundError,
    ParsingService,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter()


# ============================================================
# CONSTANTS
# ============================================================

DEFAULT_PAGE_SIZE = 30
MAX_PAGE_SIZE = 100


# ============================================================
# DEPENDENCIES
# ============================================================


def get_parsing_service(
    db=Depends(database_session),
) -> ParsingService:
    """
    Build the Module 03 parsing service.

    Module 03 depends on:

        EmailRepository
            ↓
        Module 02 canonical email source

        ParsingRepository
            ↓
        Module 03 parsed-result persistence
    """

    return ParsingService(
        email_repository=EmailRepository(db),
        parsing_repository=ParsingRepository(db),
    )


ParsingReader = Annotated[
    object,
    Depends(
        require_permission(
            Permission.EMAILS_READ,
        ),
    ),
]


ParsingServiceDependency = Annotated[
    ParsingService,
    Depends(get_parsing_service),
]


# ============================================================
# HEALTH
# ============================================================


@router.get(
    "/health",
    summary="Parsing module health check",
)
def parsing_health() -> dict[str, str]:
    """
    Return Module 03 health status.
    """

    return {
        "module": "parsing",
        "status": "ready",
    }


# ============================================================
# GLOBAL PARSING SUMMARY
# ============================================================


@router.get(
    "/summary",
    response_model=ParsingPersistenceSummary,
    summary="Get global parsing summary",
)
def get_parsing_summary(
    current_user: ParsingReader,
    service: ParsingServiceDependency,
) -> ParsingPersistenceSummary:
    """
    Return the complete global Module 03 parsing state.

    The result is independent of:

        - search
        - filters
        - pagination
        - current UI page

    Example:

        total_collected = 52
        total_parsed = 22
        total_pending = 30
        total_warnings = 0
        total_failed = 0
        ready_for_features = 22
        readiness_percentage = 42.31
    """

    return service.get_parsing_summary()


# ============================================================
# LIST PARSING WORKSPACE
# ============================================================


@router.get(
    "/emails",
    response_model=ParsingEmailListResponse,
    summary="List collected emails for the Parsing Workspace",
)
def list_parsing_emails(
    page: int = Query(
        default=1,
        ge=1,
        description="1-based page number.",
    ),
    page_size: int = Query(
        default=DEFAULT_PAGE_SIZE,
        ge=1,
        le=MAX_PAGE_SIZE,
        description="Number of emails displayed on one page.",
    ),
    search: str | None = Query(
        default=None,
        min_length=1,
        max_length=512,
        description=(
            "Search subject, sender, Message-ID, "
            "or source identifier."
        ),
    ),
    source: EmailSource | None = Query(
        default=None,
        description="Filter by email source.",
    ),
    level: EmailGroundTruthLabel | None = Query(
        default=None,
        description="Filter by ground-truth level.",
    ),
    parsing_status: ParsingStatusSchema | None = Query(
        default=None,
        alias="status",
        description="Filter by Module 03 parsing status.",
    ),
    from_date: str | None = Query(
        default=None,
        description=(
            "Filter emails received on or after this date. "
            "Format: YYYY-MM-DD."
        ),
    ),
    to_date: str | None = Query(
        default=None,
        description=(
            "Filter emails received on or before this date. "
            "Format: YYYY-MM-DD."
        ),
    ),
    current_user: ParsingReader = None,
    service: ParsingServiceDependency = None,
) -> ParsingEmailListResponse:
    """
    Return the filtered Parsing Workspace.

    Final filter layout:

        Search
        Source
        Level
        Status
        From
        To
        Reset Filters

    Filter semantics:

        Different filters = AND

        Search fields = OR

    Final table:

        Subject
        Sender
        Source
        Level
        Received
        Status
        Action

    Important architecture rule:

        Module 02 Email
                ↓
        LEFT JOIN Module 03 ParsedEmail
                ↓
        Parsing Workspace

    Therefore pending emails are also displayed.
    """

    # --------------------------------------------------------
    # Parse date query parameters.
    # --------------------------------------------------------

    from datetime import date

    parsed_from_date: date | None = None
    parsed_to_date: date | None = None

    if from_date is not None:
        try:
            parsed_from_date = date.fromisoformat(
                from_date,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="from_date must use YYYY-MM-DD format.",
            ) from exc

    if to_date is not None:
        try:
            parsed_to_date = date.fromisoformat(
                to_date,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="to_date must use YYYY-MM-DD format.",
            ) from exc

    if (
        parsed_from_date is not None
        and parsed_to_date is not None
        and parsed_from_date > parsed_to_date
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "from_date must be earlier than or equal to "
                "to_date."
            ),
        )

    # --------------------------------------------------------
    # Query filtered workspace.
    # --------------------------------------------------------

    items, total = service.list_emails(
        page=page,
        page_size=page_size,
        search=search,
        source=source,
        level=level,
        status=parsing_status,
        from_date=parsed_from_date,
        to_date=parsed_to_date,
    )

    # --------------------------------------------------------
    # Pagination metadata.
    # --------------------------------------------------------

    total_pages = max(
        1,
        (total + page_size - 1) // page_size,
    )

    if total == 0:
        start_index = 0
        end_index = 0
    else:
        start_index = (
            (page - 1) * page_size
        ) + 1

        end_index = min(
            page * page_size,
            total,
        )

    return ParsingEmailListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        start_index=start_index,
        end_index=end_index,
    )


# ============================================================
# GET MATCHING EMAIL IDS
# ============================================================


@router.get(
    "/emails/matching/ids",
    response_model=list[UUID],
    summary="Get all email IDs matching Parsing Workspace filters",
)
def get_matching_email_ids(
    search: str | None = Query(
        default=None,
        min_length=1,
        max_length=512,
    ),
    source: EmailSource | None = Query(
        default=None,
    ),
    level: EmailGroundTruthLabel | None = Query(
        default=None,
    ),
    parsing_status: ParsingStatusSchema | None = Query(
        default=None,
        alias="status",
    ),
    from_date: str | None = Query(
        default=None,
    ),
    to_date: str | None = Query(
        default=None,
    ),
    current_user: ParsingReader = None,
    service: ParsingServiceDependency = None,
) -> list[UUID]:
    """
    Return every source email ID matching the active filters.

    This endpoint is intentionally not paginated.

    It supports:

        Select All Matching

    The returned IDs can span multiple UI pages.
    """

    from datetime import date

    parsed_from_date: date | None = None
    parsed_to_date: date | None = None

    if from_date is not None:
        try:
            parsed_from_date = date.fromisoformat(
                from_date,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="from_date must use YYYY-MM-DD format.",
            ) from exc

    if to_date is not None:
        try:
            parsed_to_date = date.fromisoformat(
                to_date,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="to_date must use YYYY-MM-DD format.",
            ) from exc

    if (
        parsed_from_date is not None
        and parsed_to_date is not None
        and parsed_from_date > parsed_to_date
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "from_date must be earlier than or equal to "
                "to_date."
            ),
        )

    return service.get_matching_email_ids(
        search=search,
        source=source,
        level=level,
        status=parsing_status,
        from_date=parsed_from_date,
        to_date=parsed_to_date,
    )


# ============================================================
# GET PENDING EMAIL IDS
# ============================================================


@router.get(
    "/emails/pending/ids",
    response_model=list[UUID],
    summary="Get all pending email IDs",
)
def get_pending_email_ids(
    search: str | None = Query(
        default=None,
        min_length=1,
        max_length=512,
    ),
    source: EmailSource | None = Query(
        default=None,
    ),
    level: EmailGroundTruthLabel | None = Query(
        default=None,
    ),
    from_date: str | None = Query(
        default=None,
    ),
    to_date: str | None = Query(
        default=None,
    ),
    current_user: ParsingReader = None,
    service: ParsingServiceDependency = None,
) -> list[UUID]:
    """
    Return all pending source email IDs.

    Pending means:

        Module 02 Email exists
        AND
        Module 03 ParsedEmail does not exist.

    This endpoint is not paginated.
    """

    from datetime import date

    parsed_from_date: date | None = None
    parsed_to_date: date | None = None

    if from_date is not None:
        try:
            parsed_from_date = date.fromisoformat(
                from_date,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="from_date must use YYYY-MM-DD format.",
            ) from exc

    if to_date is not None:
        try:
            parsed_to_date = date.fromisoformat(
                to_date,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="to_date must use YYYY-MM-DD format.",
            ) from exc

    if (
        parsed_from_date is not None
        and parsed_to_date is not None
        and parsed_from_date > parsed_to_date
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "from_date must be earlier than or equal to "
                "to_date."
            ),
        )

    return service.get_pending_email_ids(
        search=search,
        source=source,
        level=level,
        from_date=parsed_from_date,
        to_date=parsed_to_date,
    )


# ============================================================
# BATCH PARSE — EXPLICIT EMAIL IDS
# ============================================================


@router.post(
    "/emails/parse",
    response_model=list[ParsedEmailResponse],
    status_code=status.HTTP_200_OK,
    summary="Parse multiple selected collected emails",
)
def parse_emails(
    request: ParseEmailsRequest,
    current_user: ParsingReader = None,
    service: ParsingServiceDependency = None,
) -> list[ParsedEmailResponse]:
    """
    Parse explicitly selected collected emails.

    Maximum request size is controlled by ParseEmailsRequest.

    Processing flow:

        email_ids
            ↓
        Module 02 EmailRepository
            ↓
        EmailParser
            ↓
        Normalizer
            ↓
        Validator
            ↓
        parsed_emails UPSERT
            ↓
        structured responses
    """

    try:
        return service.parse_and_validate_emails(
            request.email_ids,
        )

    except ParsingEmailNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


# ============================================================
# PARSE ALL MATCHING
# ============================================================


@router.post(
    "/emails/parse/matching",
    response_model=list[ParsedEmailResponse],
    status_code=status.HTTP_200_OK,
    summary="Parse all emails matching the active filters",
)
def parse_matching_emails(
    request: ParseMatchingEmailsRequest,
    current_user: ParsingReader = None,
    service: ParsingServiceDependency = None,
) -> list[ParsedEmailResponse]:
    """
    Parse every email matching the supplied filters.

    Pagination is intentionally ignored.

    This operation is designed for:

        Parse Selected
        Parse All Matching

    Large datasets should eventually be executed through a
    background job while preserving this same service contract.
    """

    try:
        return service.parse_matching_emails(
            search=request.search,
            source=request.source,
            level=request.level,
            status=request.status,
            from_date=request.from_date,
            to_date=request.to_date,
        )

    except ParsingEmailNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


# ============================================================
# PARSE ALL PENDING
# ============================================================


@router.post(
    "/emails/parse/pending",
    response_model=list[ParsedEmailResponse],
    status_code=status.HTTP_200_OK,
    summary="Parse all pending emails",
)
def parse_all_pending(
    request: ParseAllPendingRequest,
    current_user: ParsingReader = None,
    service: ParsingServiceDependency = None,
) -> list[ParsedEmailResponse]:
    """
    Parse all currently pending emails.

    Optional filters can narrow the pending population.

    Pagination is ignored.

    The UI action is:

        Parse All Pending
    """

    if not request.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Parsing all pending emails requires "
                "explicit confirmation."
            ),
        )

    try:
        return service.parse_all_pending()

    except ParsingEmailNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


# ============================================================
# GET PERSISTED PARSED EMAIL
# ============================================================


@router.get(
    "/emails/{email_id}",
    response_model=ParsedEmailResponse,
    summary="Get persisted parsed email",
)
def get_parsed_email(
    email_id: UUID,
    current_user: ParsingReader = None,
    service: ParsingServiceDependency = None,
) -> ParsedEmailResponse:
    """
    Return the persisted Module 03 parsing result.

    IMPORTANT:

        GET does NOT execute the parser again.

    If the email has not been parsed yet, HTTP 404 is returned.

    Parsing is explicitly triggered through:

        POST /emails/{email_id}/parse
    """

    try:
        return service.get_parsed_email(
            email_id,
        )

    except ParsingEmailNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


# ============================================================
# PARSE SINGLE EMAIL
# ============================================================


@router.post(
    "/emails/{email_id}/parse",
    response_model=ParsedEmailResponse,
    status_code=status.HTTP_200_OK,
    summary="Parse one collected email",
)
def parse_email(
    email_id: UUID,
    current_user: ParsingReader = None,
    service: ParsingServiceDependency = None,
) -> ParsedEmailResponse:
    """
    Parse one collected email and persist the result.

    Existing parsed results are updated through repository
    upsert instead of creating duplicate rows.
    """

    try:
        return service.parse_and_validate_email(
            email_id,
        )

    except ParsingEmailNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc