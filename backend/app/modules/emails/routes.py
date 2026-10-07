from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)

from app.common.dependencies import database_session
from app.core.permissions import Permission
from app.core.rbac import require_permission
from app.modules.audit_security_admin.administration.settings_manager import get_effective_setting

from .models import EmailGroundTruthLabel, EmailSource
from .repository import EmailRepository
from .schemas import (
    EmailBulkUploadResponse,
    EmailDetailResponse,
    EmailIngestRequest,
    EmailListQuery,
    EmailListResponse,
    EmailResponse,
    EmailStatisticsResponse,
)
from .service import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    EmailAlreadyExistsError,
    EmailIngestionError,
    EmailNotFoundError,
    EmailService,
)


router = APIRouter()


# ============================================================
# DEPENDENCIES
# ============================================================


def get_email_service(
    db=Depends(database_session),
) -> EmailService:
    """
    Build the EmailService with its database repository.
    """

    return EmailService(
        repository=EmailRepository(db),
    )


EmailReader = Annotated[
    object,
    Depends(
        require_permission(
            Permission.EMAILS_READ,
        ),
    ),
]


EmailIngester = Annotated[
    object,
    Depends(
        require_permission(
            Permission.EMAILS_INGEST,
        ),
    ),
]


EmailServiceDependency = Annotated[
    EmailService,
    Depends(get_email_service),
]


# ============================================================
# RAW EMAIL INGESTION
# ============================================================


@router.post(
    "/ingest",
    response_model=EmailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a raw email",
)
def ingest_email(
    payload: EmailIngestRequest,
    current_user: EmailIngester,
    service: EmailServiceDependency,
) -> EmailResponse:
    """
    Ingest one raw email.

    The ground-truth label must be supplied by the caller.

    Source is always RAW_EMAIL for this endpoint.
    """

    try:
        email = service.ingest(
            payload,
        )

        return service._to_email_response(
            email,
        )

    except EmailAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except EmailIngestionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


# ============================================================
# SINGLE .EML FILE UPLOAD
# ============================================================


@router.post(
    "/upload",
    response_model=EmailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload one .eml file",
)
def upload_email(
    file: Annotated[
        UploadFile,
        File(...),
    ],
    ground_truth_label: Annotated[
        EmailGroundTruthLabel,
        Query(
            description=(
                "Ground-truth label assigned to the uploaded email."
            ),
        ),
    ],
    current_user: EmailIngester,
    service: EmailServiceDependency,
) -> EmailResponse:
    """
    Upload and ingest one .eml file.

    Supported labels:

        NORMAL
        BOMBING
    """

    filename = (
        file.filename or ""
    ).strip()

    if not filename:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A filename is required.",
        )

    if not filename.lower().endswith(".eml"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only .eml files are supported.",
        )

    try:
        max_bytes = int(get_effective_setting(service.repository.db, "email.max_upload_mb") or 20) * 1_000_000
        raw_data = file.file.read(max_bytes + 1)
        if len(raw_data) > max_bytes:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=f"Email file exceeds the configured {max_bytes // 1_000_000} MB limit.")

        email = service.ingest_file(
            raw_data,
            ground_truth_label=ground_truth_label,
            source_identifier=filename,
        )

        return service._to_email_response(
            email,
        )

    except EmailAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except EmailIngestionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


# ============================================================
# BULK .EML FILE UPLOAD
# ============================================================


@router.post(
    "/upload/bulk",
    response_model=EmailBulkUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload multiple .eml files",
)
def upload_emails_bulk(
    files: Annotated[
        list[UploadFile],
        File(...),
    ],
    ground_truth_label: Annotated[
        EmailGroundTruthLabel,
        Query(
            description=(
                "Ground-truth label applied to every file "
                "in this batch."
            ),
        ),
    ],
    current_user: EmailIngester,
    service: EmailServiceDependency,
) -> EmailBulkUploadResponse:
    """
    Upload multiple .eml files in one batch.

    Every file in the batch receives the same ground-truth
    label.

    NORMAL and BOMBING files must not be mixed in one batch.
    """

    if not files:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one .eml file is required.",
        )

    prepared_files: list[
        tuple[str, bytes]
    ] = []

    for file in files:
        filename = (
            file.filename or ""
        ).strip()

        if not filename:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Every uploaded file must have a filename.",
            )

        if not filename.lower().endswith(".eml"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Unsupported file '{filename}'. "
                    "Only .eml files are supported."
                ),
            )

        try:
            max_bytes = int(get_effective_setting(service.repository.db, "email.max_upload_mb") or 20) * 1_000_000
            raw_data = file.file.read(max_bytes + 1)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Failed to read uploaded file '{filename}'."
                ),
            ) from exc

        if len(raw_data) > max_bytes:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=f"Email file '{filename}' exceeds the configured {max_bytes // 1_000_000} MB limit.")

        if not raw_data:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Uploaded file '{filename}' is empty."
                ),
            )

        prepared_files.append(
            (
                filename,
                raw_data,
            )
        )

    try:
        return service.ingest_files(
            prepared_files,
            ground_truth_label=ground_truth_label,
        )

    except EmailIngestionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


# ============================================================
# EMAIL LIST / FILTERS
# ============================================================


@router.get(
    "",
    response_model=EmailListResponse,
    summary="List emails",
)
def list_emails(
    current_user: EmailReader,
    service: EmailServiceDependency,
    page: int = Query(
        default=1,
        ge=1,
        description="Page number.",
    ),
    page_size: int = Query(
        default=DEFAULT_PAGE_SIZE,
        ge=1,
        le=MAX_PAGE_SIZE,
        description="Number of emails per page.",
    ),
    search: str | None = Query(
        default=None,
        description=(
            "Search subject, sender, recipients, "
            "source identifier, or Message-ID."
        ),
    ),
    source: EmailSource | None = Query(
        default=None,
        description="Filter by email source.",
    ),
    status: EmailGroundTruthLabel | None = Query(
        default=None,
        description=(
            "Filter by ground-truth status: "
            "NORMAL or BOMBING."
        ),
    ),
    from_date: str | None = Query(
        default=None,
        description=(
            "Inclusive lower received-at date/time."
        ),
    ),
    to_date: str | None = Query(
        default=None,
        description=(
            "Inclusive upper received-at date/time."
        ),
    ),
) -> EmailListResponse:
    """
    Return filtered and paginated emails.

    All supplied filters are combined using AND semantics.

    UI mapping:

        Search
        Source
        Status
        From
        To
    """

    parsed_from_date = _parse_datetime(
        from_date,
        field_name="from_date",
    )

    parsed_to_date = _parse_datetime(
        to_date,
        field_name="to_date",
    )

    if (
        parsed_from_date is not None
        and parsed_to_date is not None
        and parsed_from_date > parsed_to_date
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "from_date cannot be later than to_date."
            ),
        )

    query = EmailListQuery(
        page=page,
        page_size=page_size,
        search=search,
        source=source,
        status=status,
        from_date=parsed_from_date,
        to_date=parsed_to_date,
    )

    return service.get_list_response(
        query,
    )


# ============================================================
# EMAIL STATISTICS
# ============================================================


@router.get(
    "/statistics",
    response_model=EmailStatisticsResponse,
    summary="Get email statistics",
)
def get_email_statistics(
    current_user: EmailReader,
    service: EmailServiceDependency,
) -> EmailStatisticsResponse:
    """
    Return Email Management statistics.

    Includes:

        Total Emails
        Normal
        Bombing
    """

    return service.get_statistics()


# ============================================================
# EMAIL DETAIL
# ============================================================


@router.get(
    "/{email_id}",
    response_model=EmailDetailResponse,
    summary="Get email details",
)
def get_email(
    email_id: UUID,
    current_user: EmailReader,
    service: EmailServiceDependency,
) -> EmailDetailResponse:
    """
    Return complete email details for the right-side detail drawer.
    """

    try:
        return service.get_detail(
            email_id,
        )

    except EmailNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

# ============================================================
# DATETIME PARSER
# ============================================================


def _parse_datetime(
    value: str | None,
    *,
    field_name: str,
):
    """
    Parse an ISO-8601 datetime string.

    Examples accepted:

        2026-09-25
        2026-09-25T00:00:00
        2026-09-25T00:00:00+00:00
    """

    if value is None:
        return None

    normalized = value.strip()

    if not normalized:
        return None

    from datetime import datetime

    try:
        parsed = datetime.fromisoformat(
            normalized,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Invalid {field_name}. "
                "Use ISO-8601 date/time format."
            ),
        ) from exc

    return parsed
