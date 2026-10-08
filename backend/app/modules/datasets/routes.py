
from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    status,
)
from app.core.rbac import require_module_access
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.datasets.repository import DatasetRepository
from app.modules.datasets.schemas import (
    DatasetCreateRequest,
    DatasetDetailResponse,
    DatasetEmailAddRequest,
    DatasetEmailAddResponse,
    DatasetEmailDetailResponse,
    DatasetEmailListResponse,
    DatasetEmailRemoveRequest,
    DatasetEmailRemoveResponse,
    DatasetListResponse,
    DatasetSelectionRequest,
    DatasetSelectionResponse,
    DatasetSummary,
    DatasetUpdateRequest,
    DatasetValidationHistoryResponse,
    DatasetValidationResponse,
    DatasetVersionCreateRequest,
    DatasetVersionDetailResponse,
    DatasetVersionListResponse,
    DatasetWorkspaceFilters,
    DatasetWorkspaceResponse,
)
from app.modules.datasets.service import (
    DatasetExportResult,
    DatasetService,
)
from app.modules.datasets.validators import DatasetValidationError


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    tags=["Dataset Management"],
    dependencies=[Depends(require_module_access("datasets"))],
)


# ============================================================
# DEPENDENCIES
# ============================================================

def get_dataset_service(
    db: Session = Depends(get_db),
) -> DatasetService:
    """
    Build the DatasetService dependency for the current request.
    """
    repository = DatasetRepository(db)
    return DatasetService(repository)


# ============================================================
# ERROR HANDLING
# ============================================================

def _raise_dataset_error(
    exc: DatasetValidationError,
) -> None:
    """
    Convert dataset validation errors into HTTP 400 responses.
    """
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(exc),
    ) from exc


# ============================================================
# HEALTH
# ============================================================

@router.get(
    "/health",
    summary="Dataset Module Health",
)
def dataset_health() -> dict[str, Any]:
    """
    Return Dataset Management module health information.
    """
    return {
        "module": "dataset-management",
        "status": "ok",
        "feature_schema": "F1-F12",
        "export_formats": [
            "csv",
            "json",
        ],
        "splits": [
            "all",
            "train",
            "validation",
            "test",
        ],
    }


# ============================================================
# WORKSPACE
# ============================================================

@router.get(
    "",
    response_model=DatasetWorkspaceResponse,
    summary="Get Dataset Workspace",
)
def get_dataset_workspace(
    search: str | None = Query(
        default=None,
        description=(
            "Search by subject, sender, Message-ID, "
            "or source identifier."
        ),
    ),
    ground_truth: str | None = Query(
        default=None,
        description="Filter by normal or bombing.",
    ),
    source: str | None = Query(
        default=None,
        description="Filter by file upload or raw email.",
    ),
    from_date: str | None = Query(
        default=None,
        description="Inclusive received-at lower date.",
    ),
    to_date: str | None = Query(
        default=None,
        description="Inclusive received-at upper date.",
    ),
    page: int = Query(
        default=1,
        ge=1,
        description="1-based page number.",
    ),
    page_size: int = Query(
        default=30,
        ge=1,
        le=100,
        description="Number of rows per page.",
    ),
    service: DatasetService = Depends(get_dataset_service),
) -> DatasetWorkspaceResponse:
    """
    Return the paginated Dataset Workspace.
    """
    filters = DatasetWorkspaceFilters(
        search=search,
        ground_truth=ground_truth,
        source=source,
        from_date=from_date,
        to_date=to_date,
    )

    try:
        return service.get_workspace(
            filters=filters,
            page=page,
            page_size=page_size,
        )
    except DatasetValidationError as exc:
        _raise_dataset_error(exc)


# ============================================================
# SUMMARY
# ============================================================

@router.get(
    "/summary",
    response_model=DatasetSummary,
    summary="Get Dataset Summary",
)
def get_dataset_summary(
    service: DatasetService = Depends(get_dataset_service),
) -> DatasetSummary:
    """
    Return Dataset Workspace summary counts.
    """
    try:
        return service.get_summary()
    except DatasetValidationError as exc:
        _raise_dataset_error(exc)


# ============================================================
# SELECTION
# ============================================================

@router.get(
    "/selection",
    response_model=DatasetSelectionResponse,
    summary="Get All Matching Dataset Samples",
)
def get_matching_dataset_samples(
    search: str | None = Query(
        default=None,
        description=(
            "Search by subject, sender, Message-ID, "
            "or source identifier."
        ),
    ),
    ground_truth: str | None = Query(
        default=None,
        description="Filter by normal or bombing.",
    ),
    source: str | None = Query(
        default=None,
        description="Filter by file upload or raw email.",
    ),
    from_date: str | None = Query(
        default=None,
        description="Inclusive received-at lower date.",
    ),
    to_date: str | None = Query(
        default=None,
        description="Inclusive received-at upper date.",
    ),
    service: DatasetService = Depends(get_dataset_service),
) -> DatasetSelectionResponse:
    """
    Return all matching email IDs for the current filters.
    """
    filters = DatasetWorkspaceFilters(
        search=search,
        ground_truth=ground_truth,
        source=source,
        from_date=from_date,
        to_date=to_date,
    )

    try:
        email_ids = service.get_matching_email_ids(filters)
        total = len(email_ids)

        return DatasetSelectionResponse(
            total_matching=total,
            total_selectable=total,
            email_ids=email_ids,
            filters=filters,
        )
    except DatasetValidationError as exc:
        _raise_dataset_error(exc)


@router.post(
    "/selection",
    response_model=DatasetSelectionResponse,
    summary="Resolve Dataset Selection",
)
def resolve_dataset_selection(
    request: DatasetSelectionRequest,
    service: DatasetService = Depends(get_dataset_service),
) -> DatasetSelectionResponse:
    """
    Resolve and validate a Dataset selection request.
    """
    try:
        return service.get_selection(request)
    except DatasetValidationError as exc:
        _raise_dataset_error(exc)


# ============================================================
# DATASET LIST
# ============================================================

@router.get(
    "/list",
    response_model=DatasetListResponse,
    summary="List Datasets",
)
def list_datasets(
    page: int = Query(
        default=1,
        ge=1,
        description="1-based page number.",
    ),
    page_size: int = Query(
        default=30,
        ge=1,
        le=100,
        description="Number of datasets per page.",
    ),
    service: DatasetService = Depends(get_dataset_service),
) -> DatasetListResponse:
    """
    Return the paginated Dataset list.
    """
    try:
        return service.list_datasets(
            page=page,
            page_size=page_size,
        )
    except DatasetValidationError as exc:
        _raise_dataset_error(exc)


# ============================================================
# DATASET CREATE
# ============================================================

@router.post(
    "",
    response_model=DatasetDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Dataset",
)
def create_dataset(
    request: DatasetCreateRequest,
    service: DatasetService = Depends(get_dataset_service),
) -> DatasetDetailResponse:
    """
    Create a Dataset from selected eligible emails.
    """
    try:
        dataset = service.create_dataset(request)
        return service.get_dataset(dataset.id)
    except DatasetValidationError as exc:
        _raise_dataset_error(exc)


# ============================================================
# EMAIL SAMPLE DETAIL
# ============================================================

@router.get(
    "/samples/{email_id}",
    response_model=DatasetEmailDetailResponse,
    summary="Get Dataset Sample",
)
def get_dataset_sample(
    email_id: UUID,
    service: DatasetService = Depends(get_dataset_service),
) -> DatasetEmailDetailResponse:
    """
    Return canonical email details and its F1-F12 feature vector.
    """
    try:
        return service.get_sample_detail(email_id)
    except DatasetValidationError as exc:
        _raise_dataset_error(exc)


# ============================================================
# GLOBAL DATASET VERSION LIST
#
# IMPORTANT:
# Keep this static route before /{dataset_id}.
# Otherwise, "versions" may be interpreted as a dataset UUID.
# ============================================================

@router.get(
    "/versions",
    response_model=DatasetVersionListResponse,
    summary="List All Dataset Versions",
)
def list_all_dataset_versions(
    page: int = Query(
        default=1,
        ge=1,
        description="1-based page number.",
    ),
    page_size: int = Query(
        default=30,
        ge=1,
        le=100,
        description="Number of versions per page.",
    ),
    service: DatasetService = Depends(get_dataset_service),
) -> DatasetVersionListResponse:
    """
    Return the paginated list of all Dataset Versions.
    """
    try:
        return service.list_all_dataset_versions(
            page=page,
            page_size=page_size,
        )
    except DatasetValidationError as exc:
        _raise_dataset_error(exc)


# ============================================================
# VERSION CREATE
# ============================================================

@router.post(
    "/versions",
    response_model=DatasetVersionDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Dataset Version",
)
def create_dataset_version(
    request: DatasetVersionCreateRequest,
    service: DatasetService = Depends(get_dataset_service),
) -> DatasetVersionDetailResponse:
    """
    Create an immutable Dataset Version snapshot.
    """
    try:
        result = service.create_dataset_version(request)

        return service.get_dataset_version(
            result.version.id,
        )
    except DatasetValidationError as exc:
        _raise_dataset_error(exc)


# ============================================================
# VERSION DETAIL
# ============================================================

@router.get(
    "/versions/{version_id}",
    response_model=DatasetVersionDetailResponse,
    summary="Get Dataset Version",
)
def get_dataset_version(
    version_id: UUID,
    service: DatasetService = Depends(get_dataset_service),
) -> DatasetVersionDetailResponse:
    """
    Return Dataset Version details.
    """
    try:
        return service.get_dataset_version(version_id)
    except DatasetValidationError as exc:
        _raise_dataset_error(exc)


# ============================================================
# VERSION SAMPLE IDS
# ============================================================

@router.get(
    "/versions/{version_id}/samples",
    response_model=list[UUID],
    summary="Get Dataset Version Sample IDs",
)
def get_version_sample_ids(
    version_id: UUID,
    split: str | None = Query(
        default=None,
        description="Optional: train, validation, or test.",
    ),
    service: DatasetService = Depends(get_dataset_service),
) -> list[UUID]:
    """
    Return sample IDs belonging to a Dataset Version.
    """
    try:
        return service.get_version_sample_ids(
            version_id,
            split=split,
        )
    except DatasetValidationError as exc:
        _raise_dataset_error(exc)


# ============================================================
# VERSION VALIDATION
# ============================================================

@router.post(
    "/versions/{version_id}/validate",
    response_model=DatasetValidationResponse,
    summary="Validate Dataset Version",
)
def validate_dataset_version(
    version_id: UUID,
    service: DatasetService = Depends(get_dataset_service),
) -> DatasetValidationResponse:
    """
    Validate the integrity of a Dataset Version.
    """
    try:
        return service.validate_dataset_version(version_id)
    except DatasetValidationError as exc:
        _raise_dataset_error(exc)


# ============================================================
# VERSION VALIDATION HISTORY
# ============================================================

@router.get(
    "/versions/{version_id}/validation-runs",
    response_model=DatasetValidationHistoryResponse,
    summary="List Dataset Version Validation Runs",
)
def list_validation_runs(
    version_id: UUID,
    page: int = Query(
        default=1,
        ge=1,
        description="1-based page number.",
    ),
    page_size: int = Query(
        default=30,
        ge=1,
        le=100,
        description="Number of validation runs per page.",
    ),
    service: DatasetService = Depends(get_dataset_service),
) -> DatasetValidationHistoryResponse:
    """
    Return paginated validation history for a Dataset Version.
    """
    try:
        return service.list_validation_runs(
            version_id,
            page=page,
            page_size=page_size,
        )
    except DatasetValidationError as exc:
        _raise_dataset_error(exc)


# ============================================================
# EXPORT PREVIEW
# ============================================================

@router.get(
    "/versions/{version_id}/export/preview",
    summary="Preview Dataset Export",
)
def preview_dataset_export(
    version_id: UUID,
    split: str = Query(
        default="all",
        description="all, train, validation, or test.",
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Maximum preview rows.",
    ),
    service: DatasetService = Depends(get_dataset_service),
) -> dict[str, Any]:
    """
    Preview rows from a Dataset Version export.
    """
    try:
        return service.preview_dataset_export(
            version_id,
            split=split,
            limit=limit,
        )
    except DatasetValidationError as exc:
        _raise_dataset_error(exc)


# ============================================================
# EXPORT
# ============================================================

@router.get(
    "/versions/{version_id}/export",
    summary="Export Dataset Version",
)
def export_dataset_version(
    version_id: UUID,
    export_format: str = Query(
        default="csv",
        alias="format",
        description="csv or json.",
    ),
    split: str = Query(
        default="all",
        description="all, train, validation, or test.",
    ),
    service: DatasetService = Depends(get_dataset_service),
) -> Response:
    """
    Export a Dataset Version in CSV or JSON format.
    """
    try:
        result: DatasetExportResult = service.export_dataset_version(
            version_id,
            export_format=export_format,
            split=split,
        )

        return Response(
            content=result.content,
            media_type=result.content_type,
            headers={
                "Content-Disposition": (
                    f'attachment; filename="{result.filename}"'
                ),
                "X-Dataset-Sample-Count": str(
                    result.sample_count,
                ),
            },
        )
    except DatasetValidationError as exc:
        _raise_dataset_error(exc)


# ============================================================
# EXPORT METADATA
# ============================================================

@router.get(
    "/versions/{version_id}/export/metadata",
    summary="Get Dataset Export Metadata",
)
def get_export_metadata(
    version_id: UUID,
    export_format: str = Query(
        default="csv",
        alias="format",
        description="csv or json.",
    ),
    split: str = Query(
        default="all",
        description="all, train, validation, or test.",
    ),
    service: DatasetService = Depends(get_dataset_service),
) -> dict[str, Any]:
    """
    Return metadata and statistics for a Dataset Version export.
    """
    try:
        result = service.export_dataset_version(
            version_id,
            export_format=export_format,
            split=split,
        )

        return result.metadata
    except DatasetValidationError as exc:
        _raise_dataset_error(exc)


# ============================================================
# DATASET EMAIL LIST
# ============================================================

@router.get(
    "/{dataset_id}/emails",
    response_model=DatasetEmailListResponse,
    summary="List Dataset Emails",
)
def list_dataset_emails(
    dataset_id: UUID,
    page: int = Query(
        default=1,
        ge=1,
        description="1-based page number.",
    ),
    page_size: int = Query(
        default=30,
        ge=1,
        le=100,
        description="Number of emails per page.",
    ),
    search: str | None = Query(
        default=None,
        description="Search Dataset emails by subject or sender.",
    ),
    service: DatasetService = Depends(get_dataset_service),
) -> DatasetEmailListResponse:
    """
    Return the paginated emails belonging to a Dataset.
    """
    try:
        return service.list_dataset_emails(
            dataset_id=dataset_id,
            page=page,
            page_size=page_size,
            search=search,
        )
    except DatasetValidationError as exc:
        _raise_dataset_error(exc)


# ============================================================
# DATASET EMAIL ADD
# ============================================================

@router.post(
    "/{dataset_id}/emails",
    response_model=DatasetEmailAddResponse,
    status_code=status.HTTP_200_OK,
    summary="Add Emails to Dataset",
)
def add_dataset_emails(
    dataset_id: UUID,
    request: DatasetEmailAddRequest,
    service: DatasetService = Depends(get_dataset_service),
) -> DatasetEmailAddResponse:
    """
    Add eligible emails to a Dataset.

    Existing memberships are skipped. Canonical Email records
    and existing Dataset Version snapshots remain unchanged.
    """
    try:
        return service.add_dataset_emails(
            dataset_id=dataset_id,
            request=request,
        )
    except DatasetValidationError as exc:
        _raise_dataset_error(exc)


# ============================================================
# DATASET EMAIL REMOVE
# ============================================================

@router.delete(
    "/{dataset_id}/emails",
    response_model=DatasetEmailRemoveResponse,
    status_code=status.HTTP_200_OK,
    summary="Remove Emails from Dataset",
)
def remove_dataset_emails(
    dataset_id: UUID,
    request: DatasetEmailRemoveRequest,
    service: DatasetService = Depends(get_dataset_service),
) -> DatasetEmailRemoveResponse:
    """
    Remove selected email memberships from a Dataset only.

    Canonical Email records, memberships in other Datasets,
    and existing Dataset Version snapshots remain untouched.
    """
    try:
        return service.remove_dataset_emails(
            dataset_id=dataset_id,
            request=request,
        )
    except DatasetValidationError as exc:
        _raise_dataset_error(exc)


# ============================================================
# DATASET DETAIL
# ============================================================

@router.get(
    "/{dataset_id}",
    response_model=DatasetDetailResponse,
    summary="Get Dataset",
)
def get_dataset(
    dataset_id: UUID,
    service: DatasetService = Depends(get_dataset_service),
) -> DatasetDetailResponse:
    """
    Return Dataset details.
    """
    try:
        return service.get_dataset(dataset_id)
    except DatasetValidationError as exc:
        _raise_dataset_error(exc)


# ============================================================
# DATASET UPDATE
# ============================================================

@router.patch(
    "/{dataset_id}",
    response_model=DatasetDetailResponse,
    summary="Update Dataset",
)
def update_dataset(
    dataset_id: UUID,
    request: DatasetUpdateRequest,
    service: DatasetService = Depends(get_dataset_service),
) -> DatasetDetailResponse:
    """
    Update the Dataset name and/or description.

    Only explicitly supplied fields are updated.
    Dataset samples and existing Dataset Versions remain unchanged.
    """
    try:
        return service.update_dataset(
            dataset_id=dataset_id,
            request=request,
        )
    except DatasetValidationError as exc:
        _raise_dataset_error(exc)


# ============================================================
# DATASET ARCHIVE
# ============================================================

@router.post(
    "/{dataset_id}/archive",
    response_model=DatasetDetailResponse,
    summary="Archive Dataset",
)
def archive_dataset(
    dataset_id: UUID,
    service: DatasetService = Depends(get_dataset_service),
) -> DatasetDetailResponse:
    """
    Archive a Dataset.
    """
    try:
        service.archive_dataset(dataset_id)
        return service.get_dataset(dataset_id)
    except DatasetValidationError as exc:
        _raise_dataset_error(exc)


# ============================================================
# DATASET VERSIONS
# ============================================================

@router.get(
    "/{dataset_id}/versions",
    response_model=DatasetVersionListResponse,
    summary="List Dataset Versions",
)
def list_dataset_versions(
    dataset_id: UUID,
    page: int = Query(
        default=1,
        ge=1,
        description="1-based page number.",
    ),
    page_size: int = Query(
        default=30,
        ge=1,
        le=100,
        description="Number of versions per page.",
    ),
    service: DatasetService = Depends(get_dataset_service),
) -> DatasetVersionListResponse:
    """
    Return the paginated version history for a Dataset.
    """
    try:
        return service.list_dataset_versions(
            dataset_id,
            page=page,
            page_size=page_size,
        )
    except DatasetValidationError as exc:
        _raise_dataset_error(exc)


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "router",
    "get_dataset_service",
    "dataset_health",
    "get_dataset_workspace",
    "get_dataset_summary",
    "get_matching_dataset_samples",
    "resolve_dataset_selection",
    "list_datasets",
    "create_dataset",
    "get_dataset_sample",
    "list_dataset_emails",
    "add_dataset_emails",
    "remove_dataset_emails",
    "get_dataset",
    "update_dataset",
    "archive_dataset",
    "list_dataset_versions",
    "list_all_dataset_versions",
    "create_dataset_version",
    "get_dataset_version",
    "get_version_sample_ids",
    "validate_dataset_version",
    "list_validation_runs",
    "preview_dataset_export",
    "export_dataset_version",
    "get_export_metadata",
]