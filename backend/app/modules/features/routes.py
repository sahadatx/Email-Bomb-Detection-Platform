from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.core.rbac import require_module_access
from sqlalchemy.orm import Session

from app.core.database import get_db

from app.modules.features.definitions import (
    FEATURE_COUNT,
    FEATURE_DEFINITIONS,
)

from app.modules.features.models import (
    FeatureExtractionStatus,
)

from app.modules.features.schemas import (
    BatchFeatureExtractionRequest,
    FeatureDefinitionListResponse,
    FeatureDefinitionResponse,
    FeatureEmailIdentity,
    FeatureEmailListItem,
    FeatureEmailListResponse,
    FeatureEmailResponse,
    FeatureEmailTimestamps,
    FeatureExtractionMetadata,
    FeatureExtractionOperationSummary,
    FeatureExtractionRequest,
    FeatureExtractionResponse,
    FeatureHealthResponse,
    FeaturePagination,
    FeatureSelectionResponse,
    FeatureSummary,
    FeatureSummaryResponse,
    FeatureValidationResult,
    FeatureValue,
    FeatureVector,
    FeatureWorkspaceFilters,
)

from app.modules.features.service import (
    EmailNotFoundError,
    FeatureExtractionError,
    FeatureService,
    ParsedEmailNotFoundError,
)


# ============================================================
# ROUTER
# ============================================================


router = APIRouter(dependencies=[Depends(require_module_access("features"))])


# ============================================================
# DEPENDENCY
# ============================================================


def get_feature_service(
    db: Session = Depends(get_db),
) -> FeatureService:
    """
    Provide the Module 04 FeatureService.
    """

    return FeatureService(db)


# ============================================================
# INTERNAL STATUS HELPERS
# ============================================================


def _public_feature_status(
    feature,
) -> str:
    """
    Convert persisted EmailFeatures status into the public
    Feature Engineering lifecycle.

    Public lifecycle:

        pending
        extracted
        warning
        failed

    Missing EmailFeatures:

        pending
    """

    if feature is None:
        return "pending"

    feature_status = feature.status

    if isinstance(
        feature_status,
        FeatureExtractionStatus,
    ):
        return feature_status.value

    return str(
        feature_status,
    ).strip().lower()


# ============================================================
# FEATURE VECTOR
# ============================================================


def _build_feature_vector(
    feature,
) -> FeatureVector:
    """
    Convert persisted EmailFeatures values into the canonical
    public F1-F12 FeatureVector.
    """

    return FeatureVector(
        f1_sender_email=feature.f1_sender_email,
        f2_known_domain=feature.f2_known_domain,
        f3_message_id=feature.f3_message_id,
        f4_auto_submitted=feature.f4_auto_submitted,
        f5_precedence_bulk=feature.f5_precedence_bulk,
        f6_list_id=feature.f6_list_id,
        f7_x_beenthere=feature.f7_x_beenthere,
        f8_x_anti_abuse=feature.f8_x_anti_abuse,
        f9_keyword_features=feature.f9_keyword_features,
        f10_subject_length=feature.f10_subject_length,
        f11_emails_per_minute=feature.f11_emails_per_minute,
        f12_emails_per_hour=feature.f12_emails_per_hour,
    )


# ============================================================
# FEATURE FIELD MAP
# ============================================================


_FEATURE_FIELD_MAP: dict[str, str] = {
    "F1": "f1_sender_email",
    "F2": "f2_known_domain",
    "F3": "f3_message_id",
    "F4": "f4_auto_submitted",
    "F5": "f5_precedence_bulk",
    "F6": "f6_list_id",
    "F7": "f7_x_beenthere",
    "F8": "f8_x_anti_abuse",
    "F9": "f9_keyword_features",
    "F10": "f10_subject_length",
    "F11": "f11_emails_per_minute",
    "F12": "f12_emails_per_hour",
}


def _feature_field_name(
    feature_id: str,
) -> str:
    """
    Convert canonical feature ID into the persisted
    FeatureVector field name.
    """

    field_name = _FEATURE_FIELD_MAP.get(
        feature_id,
    )

    if field_name is None:
        raise ValueError(
            f"Unsupported feature ID: {feature_id}",
        )

    return field_name


# ============================================================
# FEATURE VALUES
# ============================================================


def _build_feature_values(
    feature,
) -> list[FeatureValue]:
    """
    Build detailed F1-F12 FeatureValue objects.

    FEATURE_DEFINITIONS remains the authoritative source for:

        - feature name
        - description
        - data type
        - source
        - calculation
        - missing-value policy
        - normalization
    """

    vector = _build_feature_vector(
        feature,
    )

    vector_values = vector.model_dump()

    values: list[FeatureValue] = []

    for definition in FEATURE_DEFINITIONS:
        feature_id = definition.feature_id

        field_name = _feature_field_name(
            feature_id,
        )

        value = vector_values.get(
            field_name,
        )

        display_value = (
            None
            if value is None
            else str(value)
        )

        values.append(
            FeatureValue(
                feature_id=feature_id,
                feature_name=definition.name,
                value=value,
                data_type=definition.data_type.value,
                source=definition.source.value,
                status="valid",
                description=definition.description,
                calculation=definition.calculation,
                raw_value=value,
                display_value=display_value,
            )
        )

    return values


# ============================================================
# VALIDATION
# ============================================================


def _build_feature_validation(
    feature,
) -> FeatureValidationResult:
    """
    Build the public validation representation from the
    persisted extraction state.
    """

    errors = list(
        feature.validation_errors or [],
    )

    warnings = list(
        feature.validation_warnings or [],
    )

    return FeatureValidationResult(
        errors=errors,
        warnings=warnings,
        is_valid=not bool(errors),
    )


# ============================================================
# SOURCE HELPER
# ============================================================


def _get_email_source(
    email,
) -> str | None:
    """
    Return the canonical Module 02 source value.

    Supported values include:

        file_upload
        raw_email

    The value is read from Module 02 and is never fabricated
    by Module 04.
    """

    value = getattr(
        email,
        "source",
        None,
    )

    if value is None:
        return None

    if hasattr(
        value,
        "value",
    ):
        value = value.value

    return str(value)


# ============================================================
# LEVEL / GROUND-TRUTH HELPER
# ============================================================


def _get_email_level(
    email,
) -> str | None:
    """
    Return the Module 02 ground-truth label.

    IMPORTANT:

    This is dataset ground-truth metadata only.

    It is NOT:

        - prediction
        - model output
        - risk score
        - threat score
        - confidence
    """

    value = getattr(
        email,
        "ground_truth_label",
        None,
    )

    if value is None:
        return None

    if hasattr(
        value,
        "value",
    ):
        value = value.value

    return str(value)


# ============================================================
# COMPLETE FEATURE RESPONSE
# ============================================================


def _build_feature_response(
    service: FeatureService,
    email_id: UUID,
) -> FeatureEmailResponse:
    """
    Build the complete Module 04 feature response.

    Data ownership:

        Module 02
            sender
            subject
            message_id
            received_at
            collected_at
            source
            source_identifier
            ground_truth_label

        Module 03
            parsed_at

        Module 04
            F1-F12
            validation
            extraction metadata

    This response intentionally contains no:

        - prediction
        - confidence
        - risk score
        - threat score
    """

    feature = service.get_feature(
        email_id,
    )

    email = service.repository.get_email(
        email_id,
    )

    if email is None:
        raise EmailNotFoundError(
            f"Email {email_id} was not found.",
        )

    parsed = service.repository.get_parsed_email(
        email_id,
    )

    parsed_at = None

    if parsed is not None:
        parsed_at = getattr(
            parsed,
            "parsed_at",
            None,
        )

    return FeatureEmailResponse(
        id=feature.id,
        email_id=feature.email_id,

        identity=FeatureEmailIdentity(
            email_id=email.id,
            sender=email.sender,
            subject=email.subject,
            message_id=email.message_id,
            source=_get_email_source(
                email,
            ),
            source_identifier=getattr(
                email,
                "source_identifier",
                None,
            ),
            level=_get_email_level(
                email,
            ),
        ),

        timestamps=FeatureEmailTimestamps(
            received_at=email.received_at,
            collected_at=email.collected_at,
            parsed_at=parsed_at,
            extracted_at=feature.extracted_at,
        ),

        feature_vector=_build_feature_vector(
            feature,
        ),

        features=_build_feature_values(
            feature,
        ),

        validation=_build_feature_validation(
            feature,
        ),

        metadata=FeatureExtractionMetadata(
            extractor_version=feature.extractor_version,
            processing_time_ms=feature.processing_time_ms,
            status=_public_feature_status(
                feature,
            ),
            extracted_at=feature.extracted_at,
        ),
    )


# ============================================================
# PAGINATION
# ============================================================


def _build_pagination(
    *,
    page: int,
    page_size: int,
    total: int,
) -> FeaturePagination:
    """
    Build public pagination metadata.

    `total` represents the complete filtered workspace
    population, not the current page size.
    """

    if total <= 0:
        total_pages = 0
    else:
        total_pages = (
            total + page_size - 1
        ) // page_size

    return FeaturePagination(
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
        has_previous=(
            page > 1
            and total_pages > 0
        ),
        has_next=(
            total_pages > 0
            and page < total_pages
        ),
    )


# ============================================================
# FEATURE COUNT
# ============================================================


def _feature_count(
    feature,
) -> int:
    """
    Return the number of available F1-F12 values.

    A persisted EmailFeatures row represents the complete
    canonical F1-F12 vector.
    """

    if feature is None:
        return 0

    return FEATURE_COUNT


# ============================================================
# WORKSPACE ITEM
# ============================================================


def _build_workspace_item(
    email,
    parsed,
    feature,
) -> FeatureEmailListItem:
    """
    Build one Feature Workspace table row.

    Workspace population:

        ParsedEmail

    Missing EmailFeatures:

        pending

    Existing EmailFeatures:

        extracted
        warning
        failed
    """

    return FeatureEmailListItem(
        email_id=email.id,

        subject=email.subject,

        sender=email.sender,

        message_id=email.message_id,

        source=_get_email_source(
            email,
        ),

        source_identifier=getattr(
            email,
            "source_identifier",
            None,
        ),

        level=_get_email_level(
            email,
        ),

        received_at=email.received_at,

        collected_at=email.collected_at,

        parsed_at=(
            getattr(
                parsed,
                "parsed_at",
                None,
            )
            if parsed is not None
            else None
        ),

        parsed=parsed is not None,

        feature_status=_public_feature_status(
            feature,
        ),

        feature_count=_feature_count(
            feature,
        ),

        total_features=FEATURE_COUNT,

        has_features=(
            feature is not None
        ),

        updated_at=(
            feature.updated_at
            if feature is not None
            else email.updated_at
        ),
    )


# ============================================================
# FILTER NORMALIZATION
# ============================================================


def _normalize_optional_filter(
    value: str | None,
) -> str | None:
    """
    Normalize optional text filters.

    Blank strings become None.
    """

    if value is None:
        return None

    normalized = value.strip()

    return normalized or None


def _normalize_status_filter(
    value: str | None,
) -> str | None:
    """
    Normalize Feature Engineering status filters.
    """

    normalized = _normalize_optional_filter(
        value,
    )

    if normalized is None:
        return None

    return normalized.lower()


# ============================================================
# FILTER BUILDER
# ============================================================


def _build_workspace_filters(
    *,
    search: str | None,
    source: str | None,
    level: str | None,
    feature_status: str | None,
    from_date: date | None,
    to_date: date | None,
) -> FeatureWorkspaceFilters:
    """
    Build the canonical FeatureWorkspaceFilters object.

    All filtering remains owned by the repository.

    The route only normalizes and validates the API input.
    """

    normalized_search = _normalize_optional_filter(
        search,
    )

    normalized_source = _normalize_optional_filter(
        source,
    )

    normalized_level = _normalize_optional_filter(
        level,
    )

    normalized_status = _normalize_status_filter(
        feature_status,
    )

    if (
        from_date is not None
        and to_date is not None
        and from_date > to_date
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "from_date must be earlier than "
                "or equal to to_date."
            ),
        )

    return FeatureWorkspaceFilters(
        search=normalized_search,
        source=normalized_source,
        level=normalized_level,
        status=normalized_status,
        from_date=from_date,
        to_date=to_date,
    )


# ============================================================
# HEALTH
# ============================================================


@router.get(
    "/health",
    response_model=FeatureHealthResponse,
    summary="Feature engineering health",
)
def feature_health() -> FeatureHealthResponse:
    """
    Return Module 04 health and schema metadata.
    """

    return FeatureHealthResponse(
        status="healthy",
        module="feature-engineering",
        feature_schema="F1-F12",
        feature_count=FEATURE_COUNT,
    )


# ============================================================
# FEATURE DEFINITIONS
# ============================================================


@router.get(
    "/definitions",
    response_model=FeatureDefinitionListResponse,
    summary="Get F1-F12 definitions",
)
def get_feature_definitions() -> FeatureDefinitionListResponse:
    """
    Return the authoritative F1-F12 definitions.
    """

    definitions = [
        FeatureDefinitionResponse(
            feature_id=definition.feature_id,
            name=definition.name,
            description=definition.description,
            data_type=definition.data_type.value,
            source=definition.source.value,
            calculation=definition.calculation,
            missing_value=definition.missing_value,
            normalization=definition.normalization,
        )
        for definition in FEATURE_DEFINITIONS
    ]

    return FeatureDefinitionListResponse(
        definitions=definitions,
        total=len(definitions),
    )


# ============================================================
# SUMMARY
# ============================================================


@router.get(
    "/summary",
    response_model=FeatureSummaryResponse,
    summary="Get feature extraction summary",
)
def get_feature_summary(
    service: FeatureService = Depends(
        get_feature_service,
    ),
) -> FeatureSummaryResponse:
    """
    Return the global Module 04 feature extraction summary.
    """

    summary = service.get_summary()

    return FeatureSummaryResponse(
        summary=FeatureSummary(
            total_collected=summary[
                "total_collected"
            ],
            total_parsed=summary[
                "total_parsed"
            ],
            total_features_ready=summary[
                "total_features_ready"
            ],
            total_pending=summary[
                "total_pending"
            ],
            total_warnings=summary[
                "total_warnings"
            ],
            total_failed=summary[
                "total_failed"
            ],
            readiness_percentage=summary[
                "readiness_percentage"
            ],
        ),
    )


# ============================================================
# WORKSPACE
# ============================================================


@router.get(
    "/",
    response_model=FeatureEmailListResponse,
    summary="List filtered parsed emails and feature status",
)
def list_features(
    page: int = Query(
        default=1,
        ge=1,
        description="Workspace page number.",
    ),

    page_size: int = Query(
        default=30,
        ge=1,
        le=100,
        description="Workspace page size.",
    ),

    search: str | None = Query(
        default=None,
        description=(
            "Search subject, sender, Message-ID, "
            "or source identifier."
        ),
    ),

    source: str | None = Query(
        default=None,
        description="Filter by email source.",
    ),

    level: str | None = Query(
        default=None,
        description=(
            "Filter by Module 02 ground-truth level."
        ),
    ),

    feature_status: str | None = Query(
        default=None,
        alias="status",
        description=(
            "Filter by Feature Engineering status: "
            "pending, extracted, warning, failed."
        ),
    ),

    from_date: date | None = Query(
        default=None,
        description=(
            "Inclusive lower received_at date boundary."
        ),
    ),

    to_date: date | None = Query(
        default=None,
        description=(
            "Inclusive upper received_at date boundary."
        ),
    ),

    service: FeatureService = Depends(
        get_feature_service,
    ),
) -> FeatureEmailListResponse:
    """
    Return the filtered, paginated Feature Workspace.

    Supported filters:

        Search
        Source
        Level
        Status
        From
        To

    Filter semantics:

        AND

    Workspace population:

        successfully parsed emails only
    """

    filters = _build_workspace_filters(
        search=search,
        source=source,
        level=level,
        feature_status=feature_status,
        from_date=from_date,
        to_date=to_date,
    )

    rows, total = service.get_workspace(
        page=page,
        page_size=page_size,
        filters=filters,
    )

    items = [
        _build_workspace_item(
            email=email,
            parsed=parsed,
            feature=feature,
        )
        for email, parsed, feature in rows
    ]

    return FeatureEmailListResponse(
        items=items,
        pagination=_build_pagination(
            page=page,
            page_size=page_size,
            total=total,
        ),
        filters=filters,
    )


# ============================================================
# GLOBAL SELECTION
# ============================================================
#
# IMPORTANT:
#
# This route MUST appear before:
#
#     /{email_id}
#
# because "selection" must never be interpreted as UUID.
#
# ============================================================


@router.post(
    "/selection",
    response_model=FeatureSelectionResponse,
    summary="Resolve all selectable emails matching filters",
)
def resolve_feature_selection(
    filters: FeatureWorkspaceFilters,
    service: FeatureService = Depends(
        get_feature_service,
    ),
) -> FeatureSelectionResponse:
    """
    Resolve the COMPLETE selectable population matching the
    supplied Feature Workspace filters.

    This endpoint is intentionally independent from pagination.

    Example:

        filtered matching = 347
        selectable       = 312
        page size        = 30

    The response contains all 312 selectable email IDs.

    Selectable states:

        pending
        warning
        failed

    Extracted records are excluded because they do not need
    normal extraction.

    This endpoint does NOT perform extraction.
    It only resolves selection.
    """

    # --------------------------------------------------------
    # Normalize and validate the incoming filter contract.
    #
    # The frontend normally sends normalized values, but the
    # route keeps the boundary defensive.
    # --------------------------------------------------------

    normalized_filters = _build_workspace_filters(
        search=filters.search,
        source=filters.source,
        level=filters.level,
        feature_status=filters.status,
        from_date=filters.from_date,
        to_date=filters.to_date,
    )

    # --------------------------------------------------------
    # Resolve complete filtered population.
    # --------------------------------------------------------

    total_matching = (
        service.count_workspace(
            filters=normalized_filters,
        )
    )

    # --------------------------------------------------------
    # Resolve complete selectable population.
    # --------------------------------------------------------

    email_ids = (
        service.get_selectable_email_ids(
            filters=normalized_filters,
        )
    )

    total_selectable = len(
        email_ids,
    )

    return FeatureSelectionResponse(
        total_matching=total_matching,
        total_selectable=total_selectable,
        email_ids=email_ids,
        filters=normalized_filters,
    )


# ============================================================
# BATCH EXTRACTION
# ============================================================


@router.post(
    "/batch/extract",
    response_model=FeatureExtractionResponse,
    summary="Extract F1-F12 for multiple emails",
)
def extract_features_batch(
    request: BatchFeatureExtractionRequest,
    service: FeatureService = Depends(
        get_feature_service,
    ),
) -> FeatureExtractionResponse:
    """
    Extract F1-F12 for multiple selected emails.

    Each email is processed independently.

    One failed email does not stop the remaining emails.

    Duplicate email IDs are removed before processing.
    """

    # --------------------------------------------------------
    # Deduplicate while preserving request order.
    # --------------------------------------------------------

    unique_email_ids: list[UUID] = []
    seen: set[UUID] = set()

    for email_id in request.email_ids:
        if email_id in seen:
            continue

        seen.add(email_id)
        unique_email_ids.append(
            email_id,
        )

    selected = len(
        unique_email_ids,
    )

    extracted = 0
    warnings = 0
    failed = 0

    results: list[
        FeatureEmailResponse
    ] = []

    # --------------------------------------------------------
    # Process each email independently.
    # --------------------------------------------------------

    for email_id in unique_email_ids:
        try:
            feature = service.extract_features(
                email_id,
                force=request.force,
            )

            extracted += 1

            if (
                feature.status
                == FeatureExtractionStatus.WARNING
            ):
                warnings += 1

            results.append(
                _build_feature_response(
                    service,
                    email_id,
                )
            )

        except (
            EmailNotFoundError,
            ParsedEmailNotFoundError,
            FeatureExtractionError,
        ):
            failed += 1

    return FeatureExtractionResponse(
        summary=FeatureExtractionOperationSummary(
            selected=selected,
            extracted=extracted,
            warnings=warnings,
            failed=failed,
        ),
        results=results,
    )


# ============================================================
# SINGLE FEATURE DETAIL
# ============================================================


@router.get(
    "/{email_id}",
    response_model=FeatureEmailResponse,
    summary="Get F1-F12 feature details",
)
def get_feature(
    email_id: UUID,
    service: FeatureService = Depends(
        get_feature_service,
    ),
) -> FeatureEmailResponse:
    """
    Return complete F1-F12 feature details for one email.

    This endpoint requires an extracted EmailFeatures record.
    """

    try:
        return _build_feature_response(
            service,
            email_id,
        )

    except EmailNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except FeatureExtractionError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


# ============================================================
# SINGLE EXTRACTION
# ============================================================


@router.post(
    "/{email_id}/extract",
    response_model=FeatureEmailResponse,
    summary="Extract F1-F12 for an email",
)
def extract_feature(
    email_id: UUID,

    request: FeatureExtractionRequest | None = None,

    service: FeatureService = Depends(
        get_feature_service,
    ),
) -> FeatureEmailResponse:
    """
    Extract F1-F12 for one parsed email.

    Existing extracted/warning records are reused unless
    force=true is supplied.
    """

    force = (
        request.force
        if request is not None
        else False
    )

    try:
        service.extract_features(
            email_id,
            force=force,
        )

        return _build_feature_response(
            service,
            email_id,
        )

    except EmailNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except ParsedEmailNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except FeatureExtractionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


# ============================================================
# FORCE RE-EXTRACTION
# ============================================================


@router.post(
    "/{email_id}/reextract",
    response_model=FeatureEmailResponse,
    summary="Force re-extraction of F1-F12",
)
def reextract_feature(
    email_id: UUID,

    service: FeatureService = Depends(
        get_feature_service,
    ),
) -> FeatureEmailResponse:
    """
    Force a fresh F1-F12 extraction.

    Existing EmailFeatures data is updated instead of creating
    a duplicate record.
    """

    try:
        service.reextract_features(
            email_id,
        )

        return _build_feature_response(
            service,
            email_id,
        )

    except EmailNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except ParsedEmailNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except FeatureExtractionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


# ============================================================
# DELETE FEATURE RECORD
# ============================================================


@router.delete(
    "/{email_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete feature record",
)
def delete_feature(
    email_id: UUID,

    service: FeatureService = Depends(
        get_feature_service,
    ),
) -> None:
    """
    Delete only the Module 04 EmailFeatures record.

    Module 02 canonical Email data remains untouched.

    Module 03 ParsedEmail data remains untouched.
    """

    try:
        deleted = service.delete_features(
            email_id,
        )

    except EmailNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Feature record for email "
                f"{email_id} was not found."
            ),
        )

    return None