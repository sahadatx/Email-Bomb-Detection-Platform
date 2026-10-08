from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import and_, case, exists, func, or_, select
from sqlalchemy.orm import Session

from app.modules.datasets.schemas import DatasetWorkspaceFilters
from app.modules.emails.models import (
    Email,
    EmailGroundTruthLabel,
    EmailSource,
)
from app.modules.features.models import (
    EmailFeatures,
    FeatureExtractionStatus,
)
from app.modules.parsing.models import ParsedEmail


# ============================================================
# CONSTANTS
# ============================================================

FEATURE_COUNT = 12

EXPECTED_FEATURE_IDS = tuple(
    f"F{i}"
    for i in range(1, FEATURE_COUNT + 1)
)


# ============================================================
# CANONICAL ELIGIBILITY
# ============================================================

def parsed_email_exists_condition():
    """
    Check whether the email has a parsed-email record.
    """
    return (
        select(ParsedEmail.id)
        .where(ParsedEmail.email_id == Email.id)
        .correlate(Email)
        .exists()
    )


def extracted_features_exist_condition():
    """
    Check whether the email has a successfully extracted
    feature record.

    Feature extraction is owned by Module 04.
    Dataset Management does not recalculate F1-F12.
    """
    return (
        select(EmailFeatures.id)
        .where(
            EmailFeatures.email_id == Email.id,
            EmailFeatures.status == FeatureExtractionStatus.EXTRACTED,
        )
        .correlate(Email)
        .exists()
    )


def dataset_eligibility_condition():
    """
    Return the canonical Dataset eligibility condition.

    An email is eligible only if:
        1. A ParsedEmail record exists.
        2. A successfully extracted EmailFeatures record exists.
        3. Ground truth is available.

    This condition is shared by all Workspace queries.
    """
    return and_(
        parsed_email_exists_condition(),
        extracted_features_exist_condition(),
        Email.ground_truth_label.is_not(None),
    )


def build_feature_completeness_condition():
    """
    Return the canonical successful feature extraction condition.

    This verifies extraction status only. The Dataset module
    does not independently calculate feature values.
    """
    return extracted_features_exist_condition()


# ============================================================
# BASE DATASET QUERY
# ============================================================

def build_dataset_source_query(
    *,
    filters: DatasetWorkspaceFilters | None = None,
):
    """
    Build the base Dataset Workspace query.

    Returns Email ORM rows that satisfy Dataset eligibility.

    EXISTS conditions prevent duplicate Email rows if related
    tables contain multiple records for one email.
    """
    statement = (
        select(Email)
        .select_from(Email)
        .where(dataset_eligibility_condition())
    )

    return apply_dataset_workspace_filters(
        statement,
        filters=filters,
    )


# ============================================================
# FILTER APPLICATION
# ============================================================

def apply_dataset_workspace_filters(
    statement,
    *,
    filters: DatasetWorkspaceFilters | None = None,
):
    """
    Apply Dataset Workspace filters using AND semantics.

    Supported filters:
        - Search
        - Ground truth
        - Source
        - From date
        - To date

    Search fields:
        - Subject
        - Sender
        - Message-ID
        - Source identifier
    """
    if filters is None:
        return statement

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    search_value = (
        filters.search.strip()
        if filters.search
        else None
    )

    if search_value:
        pattern = f"%{search_value}%"

        statement = statement.where(
            or_(
                Email.subject.ilike(pattern),
                Email.sender.ilike(pattern),
                Email.message_id.ilike(pattern),
                Email.source_identifier.ilike(pattern),
            )
        )

    # --------------------------------------------------------
    # GROUND TRUTH
    # --------------------------------------------------------

    if filters.ground_truth is not None:
        statement = statement.where(
            Email.ground_truth_label
            == EmailGroundTruthLabel(filters.ground_truth)
        )

    # --------------------------------------------------------
    # SOURCE
    # --------------------------------------------------------

    if filters.source is not None:
        statement = statement.where(
            Email.source == EmailSource(filters.source)
        )

    # --------------------------------------------------------
    # FROM DATE
    # --------------------------------------------------------

    if filters.from_date is not None:
        statement = statement.where(
            Email.received_at >= filters.from_date
        )

    # --------------------------------------------------------
    # TO DATE
    # --------------------------------------------------------

    if filters.to_date is not None:
        statement = statement.where(
            Email.received_at <= filters.to_date
        )

    return statement


# ============================================================
# PAGINATED DATASET EMAILS
# ============================================================

def build_dataset_page_query(
    *,
    filters: DatasetWorkspaceFilters | None = None,
    page: int = 1,
    page_size: int = 30,
):
    """
    Build a paginated Dataset Workspace query.

    The default page size is 30.
    Pagination is applied only after eligibility and filters.
    """
    if page < 1:
        raise ValueError(
            "page must be greater than or equal to 1."
        )

    if page_size < 1:
        raise ValueError(
            "page_size must be greater than or equal to 1."
        )

    offset = (page - 1) * page_size

    statement = build_dataset_source_query(
        filters=filters,
    )

    return (
        statement
        .order_by(
            Email.received_at.desc(),
            Email.id.desc(),
        )
        .offset(offset)
        .limit(page_size)
    )


# ============================================================
# DATASET COUNT
# ============================================================

def build_dataset_count_query(
    *,
    filters: DatasetWorkspaceFilters | None = None,
):
    """
    Build the total count query for the filtered Workspace.

    The result is independent of pagination.
    """
    statement = (
        select(func.count(Email.id))
        .select_from(Email)
        .where(dataset_eligibility_condition())
    )

    return apply_dataset_workspace_filters(
        statement,
        filters=filters,
    )


# ============================================================
# ALL MATCHING EMAIL IDS
# ============================================================

def build_matching_email_ids_query(
    *,
    filters: DatasetWorkspaceFilters | None = None,
):
    """
    Build a query for every eligible email ID matching the
    current Workspace filters.

    No pagination is applied.

    Used for:
        - Select All Matching
        - Bulk selection
        - Dataset creation
    """
    statement = (
        select(Email.id)
        .select_from(Email)
        .where(dataset_eligibility_condition())
    )

    statement = apply_dataset_workspace_filters(
        statement,
        filters=filters,
    )

    return statement.order_by(
        Email.received_at.desc(),
        Email.id.desc(),
    )


# ============================================================
# ELIGIBILITY BY EMAIL IDS
# ============================================================

def build_eligible_email_ids_query(
    email_ids: Sequence[UUID],
):
    """
    Build a query returning eligible IDs from a supplied
    selection.

    Ineligible or nonexistent IDs are not returned.
    """
    normalized_ids = list(dict.fromkeys(email_ids))

    if not normalized_ids:
        return select(Email.id).where(False)

    return (
        select(Email.id)
        .select_from(Email)
        .where(
            Email.id.in_(normalized_ids),
            dataset_eligibility_condition(),
        )
        .order_by(
            Email.received_at.desc(),
            Email.id.desc(),
        )
    )


# ============================================================
# SINGLE EMAIL ELIGIBILITY
# ============================================================

def build_single_email_eligibility_query(
    email_id: UUID,
):
    """
    Build a query checking whether one email is eligible.
    """
    return (
        select(Email.id)
        .select_from(Email)
        .where(
            Email.id == email_id,
            dataset_eligibility_condition(),
        )
    )


# ============================================================
# GROUND TRUTH CONDITIONS
# ============================================================

def build_normal_condition():
    """
    Return the canonical Normal ground-truth condition.
    """
    return (
        Email.ground_truth_label
        == EmailGroundTruthLabel.NORMAL
    )


def build_bombing_condition():
    """
    Return the canonical Bombing ground-truth condition.
    """
    return (
        Email.ground_truth_label
        == EmailGroundTruthLabel.BOMBING
    )


# ============================================================
# SQL CASE EXPRESSIONS
# ============================================================

def case_when_normal():
    """
    Return a SQL CASE expression:

        1 -> Normal
        0 -> otherwise

    Aggregation is performed by the caller.
    """
    return case(
        (
            build_normal_condition(),
            1,
        ),
        else_=0,
    )


def case_when_bombing():
    """
    Return a SQL CASE expression:

        1 -> Bombing
        0 -> otherwise

    Aggregation is performed by the caller.
    """
    return case(
        (
            build_bombing_condition(),
            1,
        ),
        else_=0,
    )


# ============================================================
# SUMMARY QUERY
# ============================================================

def build_dataset_summary_query(
    *,
    filters: DatasetWorkspaceFilters | None = None,
):
    """
    Build the Dataset Workspace summary query.

    Returns:
        dataset_emails
        normal
        bombing

    Only eligible emails matching the filters are counted.
    """
    statement = (
        select(
            func.count(Email.id).label("dataset_emails"),
            func.coalesce(
                func.sum(case_when_normal()),
                0,
            ).label("normal"),
            func.coalesce(
                func.sum(case_when_bombing()),
                0,
            ).label("bombing"),
        )
        .select_from(Email)
        .where(dataset_eligibility_condition())
    )

    return apply_dataset_workspace_filters(
        statement,
        filters=filters,
    )


# ============================================================
# NORMAL COUNT QUERY
# ============================================================

def build_normal_count_query(
    *,
    filters: DatasetWorkspaceFilters | None = None,
):
    """
    Build a query returning the number of eligible Normal
    emails matching the filters.
    """
    statement = (
        select(func.count(Email.id))
        .select_from(Email)
        .where(
            dataset_eligibility_condition(),
            build_normal_condition(),
        )
    )

    return apply_dataset_workspace_filters(
        statement,
        filters=filters,
    )


# ============================================================
# BOMBING COUNT QUERY
# ============================================================

def build_bombing_count_query(
    *,
    filters: DatasetWorkspaceFilters | None = None,
):
    """
    Build a query returning the number of eligible Bombing
    emails matching the filters.
    """
    statement = (
        select(func.count(Email.id))
        .select_from(Email)
        .where(
            dataset_eligibility_condition(),
            build_bombing_condition(),
        )
    )

    return apply_dataset_workspace_filters(
        statement,
        filters=filters,
    )


# ============================================================
# ELIGIBLE EMAIL IDS EXECUTION
# ============================================================

def get_eligible_email_ids(
    db: Session,
    *,
    filters: DatasetWorkspaceFilters | None = None,
) -> list[UUID]:
    """
    Execute Select All Matching.

    Returns all matching eligible email IDs without
    pagination.
    """
    statement = build_matching_email_ids_query(
        filters=filters,
    )

    return list(db.scalars(statement).all())


# ============================================================
# ELIGIBILITY FOR USER SELECTION
# ============================================================

def get_eligible_email_ids_from_selection(
    db: Session,
    email_ids: Sequence[UUID],
) -> list[UUID]:
    """
    Resolve a user-provided selection against the canonical
    eligibility condition.

    The service may compare requested IDs with returned IDs
    and reject incomplete selections.
    """
    normalized_ids = list(dict.fromkeys(email_ids))

    if not normalized_ids:
        return []

    statement = build_eligible_email_ids_query(
        normalized_ids,
    )

    return list(db.scalars(statement).all())


# ============================================================
# SINGLE EMAIL ELIGIBILITY EXECUTION
# ============================================================

def is_email_dataset_eligible(
    db: Session,
    email_id: UUID,
) -> bool:
    """
    Check whether one email is currently Dataset-eligible.
    """
    statement = build_single_email_eligibility_query(
        email_id,
    )

    return db.scalar(statement) is not None


# ============================================================
# SUMMARY EXECUTION
# ============================================================

def get_dataset_summary(
    db: Session,
    *,
    filters: DatasetWorkspaceFilters | None = None,
) -> dict[str, int]:
    """
    Execute the Workspace summary query.

    The returned dictionary matches DatasetSummary.
    """
    statement = build_dataset_summary_query(
        filters=filters,
    )

    row = db.execute(statement).one()

    return {
        "dataset_emails": int(row.dataset_emails or 0),
        "normal": int(row.normal or 0),
        "bombing": int(row.bombing or 0),
    }


# ============================================================
# COUNT EXECUTION
# ============================================================

def get_dataset_count(
    db: Session,
    *,
    filters: DatasetWorkspaceFilters | None = None,
) -> int:
    """
    Execute the complete filtered Workspace count query.
    """
    statement = build_dataset_count_query(
        filters=filters,
    )

    return int(db.scalar(statement) or 0)


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "FEATURE_COUNT",
    "EXPECTED_FEATURE_IDS",
    "parsed_email_exists_condition",
    "extracted_features_exist_condition",
    "dataset_eligibility_condition",
    "build_dataset_source_query",
    "apply_dataset_workspace_filters",
    "build_dataset_page_query",
    "build_dataset_count_query",
    "build_matching_email_ids_query",
    "build_eligible_email_ids_query",
    "build_single_email_eligibility_query",
    "build_feature_completeness_condition",
    "build_normal_condition",
    "build_bombing_condition",
    "case_when_normal",
    "case_when_bombing",
    "build_dataset_summary_query",
    "build_normal_count_query",
    "build_bombing_count_query",
    "get_eligible_email_ids",
    "get_eligible_email_ids_from_selection",
    "is_email_dataset_eligible",
    "get_dataset_summary",
    "get_dataset_count",
]
