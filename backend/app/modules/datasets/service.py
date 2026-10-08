from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence
from uuid import UUID

from app.modules.datasets.exporters import (
    EXPORT_FORMAT_CSV,
    EXPORT_SPLIT_ALL,
    build_export_filename,
    build_export_metadata,
    calculate_export_statistics,
    collect_version_export_records,
    export_records,
)
from app.modules.datasets.models import (
    Dataset,
    DatasetMembership,
    DatasetSample,
    DatasetSplit,
    DatasetStatus,
    DatasetVersion,
)
from app.modules.datasets.repository import DatasetRepository
from app.modules.datasets.schemas import (
    DatasetCreateRequest,
    DatasetDetailResponse,
    DatasetEmailAddRequest,
    DatasetEmailAddResponse,
    DatasetEmailDetailResponse,
    DatasetEmailIdentity,
    DatasetEmailListItem,
    DatasetEmailListResponse,
    DatasetEmailRemoveRequest,
    DatasetEmailRemoveResponse,
    DatasetEmailTimeInformation,
    DatasetFeatureSchema,
    DatasetFeatureVector,
    DatasetListItem,
    DatasetListResponse,
    DatasetOperationResponse,
    DatasetPagination,
    DatasetSelectionRequest,
    DatasetSelectionResponse,
    DatasetSplitConfiguration,
    DatasetSplitCounts,
    DatasetSummary,
    DatasetUpdateRequest,
    DatasetValidationCheck,
    DatasetValidationIssue,
    DatasetValidationResponse,
    DatasetVersionCreateRequest,
    DatasetVersionDetailResponse,
    DatasetVersionListItem,
    DatasetVersionListResponse,
    DatasetWorkspaceFilters,
    DatasetWorkspaceItem,
    DatasetWorkspaceResponse,
    normalize_dataset_workspace_filters,
)
from app.modules.datasets.splitting import (
    SplitResult,
)
from app.modules.datasets.validators import (
    DatasetValidationError,
    validate_dataset_create_request,
    validate_dataset_version_request,
    validate_selected_email_ids,
)
from app.modules.datasets.versioning import (
    DEFAULT_FEATURE_SCHEMA_NAME,
    create_dataset_version as create_version_snapshot,
)


# ============================================================
# CONSTANTS
# ============================================================

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 30
MAX_PAGE_SIZE = 100

DEFAULT_EXPORT_FORMAT = EXPORT_FORMAT_CSV
DEFAULT_EXPORT_SPLIT = EXPORT_SPLIT_ALL

FEATURE_SCHEMA_VERSION = "F1-F12"


# ============================================================
# RESULT TYPES
# ============================================================

@dataclass(frozen=True)
class DatasetExportResult:
    """Service-level Dataset Version export result."""

    content: str
    content_type: str
    filename: str
    sample_count: int
    metadata: dict[str, Any]


@dataclass(frozen=True)
class DatasetVersionCreationResult:
    """Result returned after Dataset Version creation."""

    version: DatasetVersion
    split_result: SplitResult
    membership_count: int


# ============================================================
# DATASET SERVICE
# ============================================================

class DatasetService:
    """
    Application service for Module 05 — Dataset Management.

    Responsibilities:
        - Dataset Workspace and selection
        - Dataset creation and listing
        - Dataset editing and details
        - Dataset email membership management
        - Dataset sample details
        - Dataset Version creation
        - Dataset Version listing and details
        - Version validation
        - Dataset export and preview
        - Dataset archival

    Architectural boundaries:
        - F1-F12 values remain owned by Module 04.
        - Dataset editing changes only name and description.
        - Dataset Version snapshots remain immutable.
        - Dataset operations do not modify canonical Email records.
        - Removing a sample only removes one dataset membership.
        - This service does not perform ML predictions.
    """

    def __init__(self, repository: DatasetRepository) -> None:
        self.repository = repository

    # ========================================================
    # WORKSPACE
    # ========================================================

    def get_workspace(
        self,
        *,
        filters: DatasetWorkspaceFilters | None = None,
        page: int = DEFAULT_PAGE,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> DatasetWorkspaceResponse:
        normalized_filters = normalize_dataset_workspace_filters(
            filters
        )
        page = self._normalize_page(page)
        page_size = self._normalize_page_size(page_size)

        email_rows, total = self.repository.list_workspace(
            filters=normalized_filters,
            page=page,
            page_size=page_size,
        )

        return DatasetWorkspaceResponse(
            items=[
                self._build_workspace_item(email)
                for email in email_rows
            ],
            pagination=self._build_pagination(
                page=page,
                page_size=page_size,
                total=total,
            ),
            filters=normalized_filters,
            summary=self.get_summary(filters=normalized_filters),
        )

    def get_summary(
        self,
        *,
        filters: DatasetWorkspaceFilters | None = None,
    ) -> DatasetSummary:
        normalized_filters = normalize_dataset_workspace_filters(
            filters
        )

        total = self.repository.count_workspace(
            filters=normalized_filters
        )

        normal_filters = self._copy_filters(
            normalized_filters,
            ground_truth="normal",
        )
        bombing_filters = self._copy_filters(
            normalized_filters,
            ground_truth="bombing",
        )

        return DatasetSummary(
            dataset_emails=total,
            normal=self.repository.count_workspace(
                filters=normal_filters
            ),
            bombing=self.repository.count_workspace(
                filters=bombing_filters
            ),
        )

    def count_workspace(
        self,
        filters: DatasetWorkspaceFilters | None = None,
    ) -> int:
        normalized_filters = normalize_dataset_workspace_filters(
            filters
        )

        return self.repository.count_workspace(
            filters=normalized_filters
        )

    def get_matching_email_ids(
        self,
        filters: DatasetWorkspaceFilters | None = None,
    ) -> list[UUID]:
        normalized_filters = normalize_dataset_workspace_filters(
            filters
        )

        return self._deduplicate_ids(
            self.repository.list_matching_email_ids(
                filters=normalized_filters
            )
        )

    # ========================================================
    # SELECTION
    # ========================================================

    def get_selection(
        self,
        request: DatasetSelectionRequest,
    ) -> DatasetSelectionResponse:
        filters = normalize_dataset_workspace_filters(
            request.filters
        )

        matching_ids = self._deduplicate_ids(
            self.repository.list_matching_email_ids(
                filters=filters
            )
        )

        validate_selected_email_ids(
            matching_ids,
            matching_ids,
        )

        return DatasetSelectionResponse(
            total_matching=len(matching_ids),
            total_selectable=len(matching_ids),
            email_ids=matching_ids,
            filters=filters,
        )

    # ========================================================
    # DATASET CREATION
    # ========================================================

    def create_dataset(
        self,
        request: DatasetCreateRequest,
    ) -> Dataset:
        """
        Create a Dataset and persist its selected source samples.

        DatasetSample stores the selected email population and
        ground-truth/schema snapshot. It does not duplicate
        canonical email content or feature values.
        """
        validate_dataset_create_request(request)

        selected_ids = self._deduplicate_ids(request.email_ids)

        if not selected_ids:
            raise DatasetValidationError(
                "At least one email must be selected."
            )

        eligible_ids = set(
            self.repository.list_eligible_email_ids(selected_ids)
        )

        invalid_ids = [
            email_id
            for email_id in selected_ids
            if email_id not in eligible_ids
        ]

        if invalid_ids:
            raise DatasetValidationError(
                "One or more selected emails are not Dataset-eligible."
            )

        emails = self.repository.get_emails_by_ids(selected_ids)
        email_map = {
            email.id: email
            for email in emails
        }

        if set(email_map) != set(selected_ids):
            raise DatasetValidationError(
                "One or more selected emails could not be found."
            )

        normal_count = 0
        bombing_count = 0
        samples: list[DatasetSample] = []

        for email_id in selected_ids:
            email = email_map[email_id]
            label = self._ground_truth_value(
                email.ground_truth_label
            )

            if label == "normal":
                normal_count += 1
            elif label == "bombing":
                bombing_count += 1
            else:
                raise DatasetValidationError(
                    f"Email {email_id} has unsupported ground truth."
                )

            samples.append(
                DatasetSample(
                    email_id=email_id,
                    ground_truth=label,
                    feature_schema_version=FEATURE_SCHEMA_VERSION,
                )
            )

        feature_schema = (
            request.feature_schema.model_dump(mode="json")
            if request.feature_schema is not None
            else self._default_feature_schema()
        )

        dataset = Dataset(
            name=request.name.strip(),
            description=(
                request.description.strip()
                if request.description
                else None
            ),
            status=DatasetStatus.ACTIVE.value,
            feature_schema=feature_schema,
            sample_count=len(selected_ids),
            normal_count=normal_count,
            bombing_count=bombing_count,
        )

        created = self.repository.create_dataset(dataset)
        self.repository.flush()

        for sample in samples:
            sample.dataset_id = created.id

        self.repository.create_dataset_samples(samples)
        self.repository.flush()

        return created

    # ========================================================
    # DATASET LIST
    # ========================================================

    def list_datasets(
        self,
        *,
        page: int = DEFAULT_PAGE,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> DatasetListResponse:
        page = self._normalize_page(page)
        page_size = self._normalize_page_size(page_size)

        dataset_rows, total = self.repository.list_datasets(
            page=page,
            page_size=page_size,
        )

        items: list[DatasetListItem] = []

        for dataset in dataset_rows:
            version_count = self.repository.count_dataset_versions(
                dataset.id
            )

            items.append(
                self._build_dataset_list_item(
                    dataset,
                    version_count=version_count,
                )
            )

        return DatasetListResponse(
            items=items,
            pagination=self._build_pagination(
                page=page,
                page_size=page_size,
                total=total,
            ),
        )

    # ========================================================
    # DATASET DETAIL
    # ========================================================

    def get_dataset(
        self,
        dataset_id: UUID,
    ) -> DatasetDetailResponse:
        dataset = self.repository.get_dataset(dataset_id)

        if dataset is None:
            raise DatasetValidationError(
                f"Dataset {dataset_id} was not found."
            )

        return DatasetDetailResponse(
            id=dataset.id,
            name=dataset.name,
            description=dataset.description,
            status=self._enum_value(dataset.status),
            sample_count=dataset.sample_count,
            normal_count=dataset.normal_count,
            bombing_count=dataset.bombing_count,
            feature_schema=self._normalize_feature_schema(
                dataset.feature_schema
            ),
            version_count=self.repository.count_dataset_versions(
                dataset_id
            ),
            created_at=dataset.created_at,
            updated_at=dataset.updated_at,
        )

    # ========================================================
    # DATASET EMAIL MANAGEMENT
    # ========================================================

    def list_dataset_emails(
        self,
        dataset_id: UUID,
        *,
        page: int = DEFAULT_PAGE,
        page_size: int = DEFAULT_PAGE_SIZE,
        search: str | None = None,
    ) -> DatasetEmailListResponse:
        """
        Return the emails belonging to one Dataset.

        Email content is read from canonical Email records.
        Ground truth is read from DatasetSample so that the
        Dataset membership retains its own label snapshot.
        """
        dataset = self.repository.get_dataset(dataset_id)

        if dataset is None:
            raise DatasetValidationError(
                f"Dataset {dataset_id} was not found."
            )

        page = self._normalize_page(page)
        page_size = self._normalize_page_size(page_size)

        rows, total = self.repository.list_dataset_samples_paginated(
            dataset_id=dataset_id,
            page=page,
            page_size=page_size,
            search=search,
        )

        email_ids = [sample.email_id for sample in rows]
        emails = self.repository.get_emails_by_ids(email_ids)
        email_map = {
            email.id: email
            for email in emails
        }

        items: list[DatasetEmailListItem] = []

        for sample in rows:
            email = email_map.get(sample.email_id)

            if email is None:
                raise DatasetValidationError(
                    f"Canonical Email {sample.email_id} "
                    "could not be found."
                )

            items.append(
                DatasetEmailListItem(
                    email_id=email.id,
                    subject=email.subject,
                    sender=email.sender,
                    message_id=email.message_id,
                    source=self._normalize_source(email.source),
                    source_identifier=email.source_identifier,
                    ground_truth=self._ground_truth_value(
                        sample.ground_truth
                    ),
                )
            )

        return DatasetEmailListResponse(
            items=items,
            pagination=self._build_pagination(
                page=page,
                page_size=page_size,
                total=total,
            ),
            dataset_id=dataset_id,
        )

    def add_dataset_emails(
        self,
        dataset_id: UUID,
        request: DatasetEmailAddRequest,
    ) -> DatasetEmailAddResponse:
        """
        Add eligible canonical emails to one Dataset.

        Existing memberships are skipped. The method does not
        modify existing DatasetVersion snapshots.
        """
        dataset = self.repository.get_dataset(dataset_id)

        if dataset is None:
            raise DatasetValidationError(
                f"Dataset {dataset_id} was not found."
            )

        requested_ids = self._deduplicate_ids(request.email_ids)

        if not requested_ids:
            raise DatasetValidationError(
                "At least one email must be selected."
            )

        existing_ids = set(
            self.repository.list_existing_dataset_email_ids(
                dataset_id=dataset_id,
                email_ids=requested_ids,
            )
        )

        new_ids = [
            email_id
            for email_id in requested_ids
            if email_id not in existing_ids
        ]

        skipped_count = len(requested_ids) - len(new_ids)

        if new_ids:
            eligible_ids = set(
                self.repository.list_eligible_email_ids(new_ids)
            )

            invalid_ids = [
                email_id
                for email_id in new_ids
                if email_id not in eligible_ids
            ]

            if invalid_ids:
                raise DatasetValidationError(
                    "One or more selected emails are not Dataset-eligible."
                )

            emails = self.repository.get_emails_by_ids(new_ids)
            email_map = {
                email.id: email
                for email in emails
            }

            if set(email_map) != set(new_ids):
                raise DatasetValidationError(
                    "One or more selected emails could not be found."
                )

            samples: list[DatasetSample] = []

            for email_id in new_ids:
                email = email_map[email_id]
                label = self._ground_truth_value(
                    email.ground_truth_label
                )

                if label not in {"normal", "bombing"}:
                    raise DatasetValidationError(
                        f"Email {email_id} has unsupported ground truth."
                    )

                samples.append(
                    DatasetSample(
                        dataset_id=dataset_id,
                        email_id=email_id,
                        ground_truth=label,
                        feature_schema_version=FEATURE_SCHEMA_VERSION,
                    )
                )

            self.repository.create_dataset_samples(samples)

        sample_count, normal_count, bombing_count = (
            self._refresh_dataset_counts(dataset)
        )

        return DatasetEmailAddResponse(
            success=True,
            message=(
                f"Added {len(new_ids)} email(s); "
                f"skipped {skipped_count} existing email(s)."
            ),
            dataset_id=dataset_id,
            added_count=len(new_ids),
            skipped_count=skipped_count,
            sample_count=sample_count,
            normal_count=normal_count,
            bombing_count=bombing_count,
        )

    def remove_dataset_emails(
        self,
        dataset_id: UUID,
        request: DatasetEmailRemoveRequest,
    ) -> DatasetEmailRemoveResponse:
        """
        Remove selected DatasetSample memberships.

        Only memberships for the supplied dataset are removed.
        Canonical Email records and version snapshots are untouched.
        """
        dataset = self.repository.get_dataset(dataset_id)

        if dataset is None:
            raise DatasetValidationError(
                f"Dataset {dataset_id} was not found."
            )

        email_ids = self._deduplicate_ids(request.email_ids)

        if not email_ids:
            raise DatasetValidationError(
                "At least one email must be selected."
            )

        removed_count = self.repository.delete_dataset_samples(
            dataset_id=dataset_id,
            email_ids=email_ids,
        )

        sample_count, normal_count, bombing_count = (
            self._refresh_dataset_counts(dataset)
        )

        return DatasetEmailRemoveResponse(
            success=True,
            message=f"Removed {removed_count} email(s) from the Dataset.",
            dataset_id=dataset_id,
            removed_count=removed_count,
            sample_count=sample_count,
            normal_count=normal_count,
            bombing_count=bombing_count,
        )

    def _refresh_dataset_counts(
        self,
        dataset: Dataset,
    ) -> tuple[int, int, int]:
        """
        Recalculate Dataset counters from its current memberships.
        """
        sample_count = self.repository.count_dataset_samples(
            dataset.id
        )

        label_counts = (
            self.repository.count_dataset_samples_by_ground_truth(
                dataset.id
            )
        )

        normal_count = int(label_counts.get("normal", 0))
        bombing_count = int(label_counts.get("bombing", 0))

        dataset.sample_count = sample_count
        dataset.normal_count = normal_count
        dataset.bombing_count = bombing_count

        self.repository.update_dataset(dataset)

        return sample_count, normal_count, bombing_count

    # ========================================================
    # DATASET UPDATE
    # ========================================================

    def update_dataset(
        self,
        dataset_id: UUID,
        request: DatasetUpdateRequest,
    ) -> DatasetDetailResponse:
        """
        Update only the dataset name and description.

        The update does not modify:
            - DatasetSample memberships
            - Original Email records
            - Original email labels
            - F1-F12 feature records
            - Existing DatasetVersion snapshots
        """
        dataset = self.repository.get_dataset(dataset_id)

        if dataset is None:
            raise DatasetValidationError(
                f"Dataset {dataset_id} was not found."
            )

        supplied_fields = request.model_fields_set

        if "name" in supplied_fields:
            name = request.name

            if name is None:
                raise DatasetValidationError(
                    "Dataset name cannot be null."
                )

            normalized_name = name.strip()

            if not normalized_name:
                raise DatasetValidationError(
                    "Dataset name cannot be empty."
                )

            dataset.name = normalized_name

        if "description" in supplied_fields:
            description = request.description

            if description is None:
                dataset.description = None
            else:
                normalized_description = description.strip()
                dataset.description = (
                    normalized_description or None
                )

        self.repository.update_dataset(dataset)

        return self.get_dataset(dataset_id)

    # ========================================================
    # EMAIL DETAIL
    # ========================================================

    def get_sample_detail(
        self,
        email_id: UUID,
    ) -> DatasetEmailDetailResponse:
        email = self.repository.get_email(email_id)

        if email is None:
            raise DatasetValidationError(
                f"Email {email_id} was not found."
            )

        if not self.repository.is_email_eligible(email_id):
            raise DatasetValidationError(
                "Email is not Dataset-eligible."
            )

        parsed_email = self.repository.get_parsed_email(email_id)
        features = self.repository.get_email_features(email_id)

        if features is None:
            raise DatasetValidationError(
                "Email has no canonical feature record."
            )

        return DatasetEmailDetailResponse(
            identity=DatasetEmailIdentity(
                email_id=email.id,
                subject=email.subject,
                sender=email.sender,
                message_id=email.message_id,
                source=self._normalize_source(email.source),
                source_identifier=email.source_identifier,
                ground_truth=self._ground_truth_value(
                    email.ground_truth_label
                ),
            ),
            time=DatasetEmailTimeInformation(
                received_at=email.received_at,
                collected_at=email.collected_at,
                parsed_at=self._get_datetime(
                    parsed_email,
                    "parsed_at",
                ),
                extracted_at=self._get_datetime(
                    features,
                    "extracted_at",
                ),
            ),
            feature_vector=DatasetFeatureVector(
                f1_sender_email=features.f1_sender_email,
                f2_known_domain=features.f2_known_domain,
                f3_message_id=features.f3_message_id,
                f4_auto_submitted=features.f4_auto_submitted,
                f5_precedence_bulk=features.f5_precedence_bulk,
                f6_list_id=features.f6_list_id,
                f7_x_beenthere=features.f7_x_beenthere,
                f8_x_anti_abuse=features.f8_x_anti_abuse,
                f9_keyword_features=features.f9_keyword_features,
                f10_subject_length=features.f10_subject_length,
                f11_emails_per_minute=features.f11_emails_per_minute,
                f12_emails_per_hour=features.f12_emails_per_hour,
            ),
            feature_schema=self._default_feature_schema_model(),
        )

    # ========================================================
    # DATASET VERSION CREATION
    # ========================================================

    def create_dataset_version(
        self,
        request: DatasetVersionCreateRequest,
    ) -> DatasetVersionCreationResult:
        validate_dataset_version_request(request)

        dataset = self.repository.get_dataset(request.dataset_id)

        if dataset is None:
            raise DatasetValidationError(
                f"Dataset {request.dataset_id} was not found."
            )

        if (
            self._enum_value(dataset.status)
            != DatasetStatus.ACTIVE.value
        ):
            raise DatasetValidationError(
                "Only active datasets can create new versions."
            )

        selected_ids = self._get_dataset_version_source_ids(
            dataset.id
        )

        if not selected_ids:
            raise DatasetValidationError(
                "Cannot create a version from an empty Dataset."
            )

        feature_schema = self._normalize_feature_schema(
            dataset.feature_schema
        )

        version, memberships, split_result = create_version_snapshot(
            repository=self.repository,
            dataset=dataset,
            email_ids=selected_ids,
            name=request.name,
            split_configuration=request.split,
            feature_schema=feature_schema,
        )

        persisted_version = self.repository.get_dataset_version(
            version.id
        )

        if persisted_version is None:
            raise DatasetValidationError(
                "Dataset Version was created but could not be reloaded."
            )

        persisted_memberships = self.repository.list_memberships(
            persisted_version.id
        )

        self.repository.flush()

        return DatasetVersionCreationResult(
            version=persisted_version,
            split_result=split_result,
            membership_count=len(persisted_memberships),
        )

    # ========================================================
    # DATASET VERSION LIST
    # ========================================================

    def list_dataset_versions(
        self,
        dataset_id: UUID,
        *,
        page: int = DEFAULT_PAGE,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> DatasetVersionListResponse:
        if self.repository.get_dataset(dataset_id) is None:
            raise DatasetValidationError(
                f"Dataset {dataset_id} was not found."
            )

        page = self._normalize_page(page)
        page_size = self._normalize_page_size(page_size)

        versions, total = self.repository.list_dataset_versions(
            dataset_id=dataset_id,
            page=page,
            page_size=page_size,
        )

        return DatasetVersionListResponse(
            items=[
                self._build_version_list_item(version)
                for version in versions
            ],
            pagination=self._build_pagination(
                page=page,
                page_size=page_size,
                total=total,
            ),
        )


    # ========================================================
    # ALL DATASET VERSIONS
    # ========================================================

    def list_all_dataset_versions(
        self,
        *,
        page: int = DEFAULT_PAGE,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> DatasetVersionListResponse:
        """Return a paginated list of versions across all datasets."""
        page = self._normalize_page(page)
        page_size = self._normalize_page_size(page_size)

        versions, total = self.repository.list_dataset_versions(
            page=page,
            page_size=page_size,
        )

        return DatasetVersionListResponse(
            items=[
                self._build_version_list_item(version)
                for version in versions
            ],
            pagination=self._build_pagination(
                page=page,
                page_size=page_size,
                total=total,
            ),
        )

    # ========================================================
    # DATASET VERSION DETAIL
    # ========================================================

    def get_dataset_version(
        self,
        version_id: UUID,
    ) -> DatasetVersionDetailResponse:
        version = self.repository.get_dataset_version(version_id)

        if version is None:
            raise DatasetValidationError(
                f"Dataset Version {version_id} was not found."
            )

        memberships = self.repository.list_memberships(version_id)

        return DatasetVersionDetailResponse(
            id=version.id,
            dataset_id=version.dataset_id,
            version_number=version.version_number,
            name=version.name,
            status=self._enum_value(version.status),
            sample_count=version.sample_count,
            normal_count=version.normal_count,
            bombing_count=version.bombing_count,
            split=self._build_split_configuration_from_version(
                version
            ),
            split_counts=self._build_split_counts(memberships),
            validation_passed=bool(version.validation_passed),
            validation_summary=version.validation_summary or {},
            feature_schema=self._normalize_feature_schema(
                version.feature_schema
            ),
            created_at=version.created_at,
            validated_at=version.validated_at,
        )

    # ========================================================
    # VERSION SAMPLE IDS
    # ========================================================

    def get_version_sample_ids(
        self,
        version_id: UUID,
        split: str | None = None,
    ) -> list[UUID]:
        version = self.repository.get_dataset_version(version_id)

        if version is None:
            raise DatasetValidationError(
                f"Dataset Version {version_id} was not found."
            )

        if split is None:
            return self.repository.list_version_email_ids(version_id)

        normalized_split = self._normalize_split(split)

        return self.repository.list_version_email_ids_by_split(
            version_id=version_id,
            split=normalized_split,
        )



    def list_validation_runs(
        self,
        version_id: UUID,
        *,
        page: int = DEFAULT_PAGE,
        page_size: int = DEFAULT_PAGE_SIZE,
    ):
        from app.modules.datasets.validation_service import ValidationService
        from app.modules.datasets.schemas import (
            DatasetValidationHistoryResponse,
            DatasetValidationRunResponse,
        )

        version = self.repository.get_version(version_id)

        if version is None:
            raise DatasetValidationError(
                f"Dataset Version {version_id} was not found."
            )

        page = self._normalize_page(page)
        page_size = self._normalize_page_size(page_size)

        validation_service = ValidationService(self.repository)

        runs, total = validation_service.list_validation_runs(
            version_id,
            page=page,
            page_size=page_size,
        )

        items = [
            DatasetValidationRunResponse(
                id=run.id,
                dataset_id=version.dataset_id,
                version_id=version.id,
                status=getattr(run.status, "value", run.status),
                overall_status=getattr(
                    run.overall_status,
                    "value",
                    run.overall_status,
                ),
                total_samples=int(run.total_samples or 0),
                error_count=int(run.error_count or 0),
                warning_count=int(run.warning_count or 0),
                passed_checks=int(run.passed_checks or 0),
                warning_checks=int(run.warning_checks or 0),
                failed_checks=int(run.failed_checks or 0),
                summary=run.summary or {},
                policy_version=run.policy_version,
                started_at=run.started_at,
                completed_at=run.completed_at,
            )
            for run in runs
        ]

        return DatasetValidationHistoryResponse(
            dataset_id=version.dataset_id,
            version_id=version.id,
            items=items,
            pagination=self._build_pagination(
                page=page,
                page_size=page_size,
                total=total,
            ),
        )


    # ========================================================
    # VALIDATION HISTORY
    # ========================================================

    def list_validation_runs(
        self,
        version_id: UUID,
        *,
        page: int = DEFAULT_PAGE,
        page_size: int = DEFAULT_PAGE_SIZE,
    ):
        from app.modules.datasets.validation_service import ValidationService
        from app.modules.datasets.schemas import (
            DatasetValidationHistoryResponse,
            DatasetValidationRunResponse,
        )

        version = self.repository.get_version(version_id)

        if version is None:
            raise DatasetValidationError(
                f"Dataset Version {version_id} was not found."
            )

        page = self._normalize_page(page)
        page_size = self._normalize_page_size(page_size)

        validation_service = ValidationService(self.repository)

        runs, total = validation_service.list_validation_runs(
            version_id,
            page=page,
            page_size=page_size,
        )

        items = [
            DatasetValidationRunResponse(
                id=run.id,
                dataset_id=version.dataset_id,
                version_id=version.id,
                status=getattr(run.status, "value", run.status),
                overall_status=getattr(
                    run.overall_status,
                    "value",
                    run.overall_status,
                ),
                total_samples=int(run.total_samples or 0),
                error_count=int(run.error_count or 0),
                warning_count=int(run.warning_count or 0),
                passed_checks=int(run.passed_checks or 0),
                warning_checks=int(run.warning_checks or 0),
                failed_checks=int(run.failed_checks or 0),
                summary=run.summary or {},
                policy_version=run.policy_version,
                started_at=run.started_at,
                completed_at=run.completed_at,
            )
            for run in runs
        ]

        return DatasetValidationHistoryResponse(
            dataset_id=version.dataset_id,
            version_id=version.id,
            items=items,
            pagination=self._build_pagination(
                page=page,
                page_size=page_size,
                total=total,
            ),
        )


    # ========================================================
    # VERSION VALIDATION
    # ========================================================


    def validate_dataset_version(
        self,
        version_id: UUID,
    ) -> DatasetValidationResponse:
        from app.modules.datasets.validation_service import ValidationService
        from app.modules.datasets.schemas import (
            DatasetValidationCheck,
            DatasetValidationIssue,
            DatasetValidationResponse,
            DatasetValidationRunResponse,
            DatasetValidationSummary,
        )

        validation_service = ValidationService(self.repository)

        run = validation_service.validate_version(version_id)
        version = self.repository.get_version(version_id)

        if version is None:
            raise DatasetValidationError(
                f"Dataset Version {version_id} was not found."
            )

        raw_summary = run.summary or {}

        checks = [
            DatasetValidationCheck(
                code=str(check.get("code", "UNKNOWN")),
                name=str(check.get("name", "Validation Check")),
                passed=bool(check.get("passed", False)),
                severity=check.get("severity", "info"),
                affected_samples=int(check.get("affected_samples", 0)),
                message=check.get("message"),
                details=check.get("details") or {},
            )
            for check in raw_summary.get("checks", [])
        ]

        issue_models = self.repository.list_all_issues(run.id)

        issues = [
            DatasetValidationIssue(
                id=issue.id,
                validation_run_id=issue.validation_run_id,
                check_code=issue.check_code,
                check_name=issue.check_name,
                severity=(
                    getattr(issue.severity, "value", issue.severity)
                ),
                title=issue.title,
                details=issue.details,
                affected_count=int(issue.affected_count or 0),
                affected_email_ids=issue.affected_email_ids or [],
                metadata=issue.metadata_json or {},
                created_at=issue.created_at,
            )
            for issue in issue_models
        ]

        summary = DatasetValidationSummary(
            total_samples=int(raw_summary.get("total_samples", 0)),
            normal_samples=int(raw_summary.get("normal_samples", 0)),
            bombing_samples=int(raw_summary.get("bombing_samples", 0)),
            total_checks=int(raw_summary.get("total_checks", 0)),
            passed_checks=int(raw_summary.get("passed_checks", 0)),
            warning_checks=int(raw_summary.get("warning_checks", 0)),
            failed_checks=int(raw_summary.get("failed_checks", 0)),
            errors=int(raw_summary.get("errors", 0)),
            warnings=int(raw_summary.get("warnings", 0)),
            overall_status=raw_summary.get("overall_status", "passed"),
        )

        run_response = DatasetValidationRunResponse(
            id=run.id,
            dataset_id=version.dataset_id,
            version_id=version.id,
            status=getattr(run.status, "value", run.status),
            overall_status=getattr(
                run.overall_status,
                "value",
                run.overall_status,
            ),
            total_samples=int(run.total_samples or 0),
            error_count=int(run.error_count or 0),
            warning_count=int(run.warning_count or 0),
            passed_checks=int(run.passed_checks or 0),
            warning_checks=int(run.warning_checks or 0),
            failed_checks=int(run.failed_checks or 0),
            summary=raw_summary,
            policy_version=run.policy_version,
            started_at=run.started_at,
            completed_at=run.completed_at,
        )

        return DatasetValidationResponse(
            dataset_id=version.dataset_id,
            version_id=version.id,
            run=run_response,
            summary=summary,
            checks=checks,
            issues=issues,
        )

    # ========================================================
    # EXPORT
    # ========================================================

    def export_dataset_version(
        self,
        version_id: UUID,
        *,
        export_format: str = DEFAULT_EXPORT_FORMAT,
        split: str = DEFAULT_EXPORT_SPLIT,
    ) -> DatasetExportResult:
        version = self.repository.get_dataset_version(version_id)

        if version is None:
            raise DatasetValidationError(
                f"Dataset Version {version_id} was not found."
            )

        records = collect_version_export_records(
            repository=self.repository,
            version=version,
            split=split,
        )

        content, content_type = export_records(
            records,
            export_format=export_format,
        )

        filename = build_export_filename(
            version=version,
            export_format=export_format,
            split=split,
        )

        metadata = build_export_metadata(
            version=version,
            export_format=export_format,
            split=split,
            sample_count=len(records),
        )
        metadata["statistics"] = calculate_export_statistics(records)

        return DatasetExportResult(
            content=content,
            content_type=content_type,
            filename=filename,
            sample_count=len(records),
            metadata=metadata,
        )

    # ========================================================
    # EXPORT PREVIEW
    # ========================================================

    def preview_dataset_export(
        self,
        version_id: UUID,
        *,
        split: str = DEFAULT_EXPORT_SPLIT,
        limit: int = 20,
    ) -> dict[str, Any]:
        version = self.repository.get_dataset_version(version_id)

        if version is None:
            raise DatasetValidationError(
                f"Dataset Version {version_id} was not found."
            )

        records = collect_version_export_records(
            repository=self.repository,
            version=version,
            split=split,
        )

        limit = max(int(limit), 1)

        return {
            "dataset_version_id": str(version.id),
            "version_number": version.version_number,
            "split": split,
            "total_samples": len(records),
            "preview_limit": limit,
            "columns": [
                "email_id",
                "ground_truth",
                "f1_sender_email",
                "f2_known_domain",
                "f3_message_id",
                "f4_auto_submitted",
                "f5_precedence_bulk",
                "f6_list_id",
                "f7_x_beenthere",
                "f8_x_anti_abuse",
                "f9_keyword_features",
                "f10_subject_length",
                "f11_emails_per_minute",
                "f12_emails_per_hour",
                "split",
            ],
            "rows": [
                self._record_to_dict(record)
                for record in records[:limit]
            ],
        }

    # ========================================================
    # ARCHIVE
    # ========================================================

    def archive_dataset(self, dataset_id: UUID) -> Dataset:
        dataset = self.repository.get_dataset(dataset_id)

        if dataset is None:
            raise DatasetValidationError(
                f"Dataset {dataset_id} was not found."
            )

        dataset.status = DatasetStatus.ARCHIVED.value
        self.repository.flush()

        return dataset

    # ========================================================
    # OPERATION RESPONSE
    # ========================================================

    @staticmethod
    def build_operation_response(
        *,
        message: str,
        success: bool = True,
        dataset_id: UUID | None = None,
        version_id: UUID | None = None,
    ) -> DatasetOperationResponse:
        return DatasetOperationResponse(
            success=success,
            message=message,
            dataset_id=dataset_id,
            version_id=version_id,
        )

    # ========================================================
    # TRANSACTION HELPERS
    # ========================================================

    def commit(self) -> None:
        self.repository.commit()

    def rollback(self) -> None:
        self.repository.rollback()

    # ========================================================
    # PRIVATE HELPERS
    # ========================================================

    @staticmethod
    def _normalize_page(page: int) -> int:
        return max(int(page), 1)

    @staticmethod
    def _normalize_page_size(page_size: int) -> int:
        return min(max(int(page_size), 1), MAX_PAGE_SIZE)

    @staticmethod
    def _build_pagination(
        *,
        page: int,
        page_size: int,
        total: int,
    ) -> DatasetPagination:
        total_pages = (
            (total + page_size - 1) // page_size
            if total > 0
            else 0
        )

        return DatasetPagination(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        )

    @staticmethod
    def _deduplicate_ids(
        email_ids: Sequence[UUID],
    ) -> list[UUID]:
        return list(dict.fromkeys(email_ids))

    @staticmethod
    def _enum_value(value: Any) -> str:
        if value is None:
            return ""

        return str(
            getattr(value, "value", value)
        ).strip().lower()

    @classmethod
    def _ground_truth_value(cls, value: Any) -> str:
        return cls._enum_value(value)

    @classmethod
    def _normalize_source(cls, value: Any) -> str:
        raw = cls._enum_value(value)

        mapping = {
            "file": "file_upload",
            "upload": "file_upload",
            "file_upload": "file_upload",
            "raw": "raw_email",
            "raw_email": "raw_email",
        }

        return mapping.get(raw, raw)

    @staticmethod
    def _get_datetime(
        obj: Any,
        attribute: str,
    ) -> Any:
        return (
            getattr(obj, attribute, None)
            if obj is not None
            else None
        )

    @staticmethod
    def _copy_filters(
        filters: DatasetWorkspaceFilters,
        *,
        ground_truth: str | None = None,
    ) -> DatasetWorkspaceFilters:
        data = filters.model_dump(mode="python")
        data["ground_truth"] = ground_truth

        return DatasetWorkspaceFilters(**data)

    @classmethod
    def _build_workspace_item(
        cls,
        email: Any,
    ) -> DatasetWorkspaceItem:
        return DatasetWorkspaceItem(
            email_id=email.id,
            subject=email.subject,
            sender=email.sender,
            ground_truth=cls._ground_truth_value(
                email.ground_truth_label
            ),
            source=cls._normalize_source(email.source),
            received_at=email.received_at,
        )

    @classmethod
    def _build_dataset_list_item(
        cls,
        dataset: Dataset,
        *,
        version_count: int = 0,
    ) -> DatasetListItem:
        return DatasetListItem(
            id=dataset.id,
            name=dataset.name,
            description=dataset.description,
            status=cls._enum_value(dataset.status),
            sample_count=dataset.sample_count,
            normal_count=dataset.normal_count,
            bombing_count=dataset.bombing_count,
            version_count=version_count,
            created_at=dataset.created_at,
            updated_at=dataset.updated_at,
        )

    @classmethod
    def _build_version_list_item(
        cls,
        version: DatasetVersion,
    ) -> DatasetVersionListItem:
        return DatasetVersionListItem(
            id=version.id,
            dataset_id=version.dataset_id,
            version_number=version.version_number,
            name=version.name,
            status=cls._enum_value(version.status),
            sample_count=version.sample_count,
            normal_count=version.normal_count,
            bombing_count=version.bombing_count,
            training_percentage=version.training_percentage,
            validation_percentage=version.validation_percentage,
            testing_percentage=version.testing_percentage,
            created_at=version.created_at,
        )

    @classmethod
    def _normalize_feature_schema(
        cls,
        value: Any,
    ) -> DatasetFeatureSchema:
        if not value:
            return cls._default_feature_schema_model()

        if isinstance(value, DatasetFeatureSchema):
            return value

        raw = dict(value)
        features = []

        for feature in raw.get("features", []):
            feature = dict(feature)

            features.append(
                {
                    "feature_id": (
                        feature.get("feature_id")
                        or feature.get("id")
                    ),
                    "name": feature.get("name", ""),
                    "data_type": feature.get(
                        "data_type",
                        "unknown",
                    ),
                }
            )

        return DatasetFeatureSchema(
            version=raw.get("version") or "1.0",
            name=raw.get("name") or DEFAULT_FEATURE_SCHEMA_NAME,
            feature_count=raw.get("feature_count") or TOTAL_FEATURES,
            features=features,
        )

    @classmethod
    def _default_feature_schema_model(
        cls,
    ) -> DatasetFeatureSchema:
        return DatasetFeatureSchema.model_validate(
            cls._default_feature_schema()
        )

    @staticmethod
    def _default_feature_schema() -> dict[str, Any]:
        definitions = [
            ("F1", "Sender Email", "string"),
            ("F2", "Known Domain Indicator", "boolean"),
            ("F3", "Message-ID Presence", "boolean"),
            ("F4", "Auto-Submitted Header", "boolean"),
            ("F5", "Precedence Bulk Indicator", "boolean"),
            ("F6", "List-Id Header", "boolean"),
            ("F7", "X-BeenThere Header", "boolean"),
            ("F8", "X-Anti-Abuse Header", "boolean"),
            ("F9", "Keyword-Based Content Features", "integer"),
            ("F10", "Subject Length", "integer"),
            ("F11", "Emails Per Minute", "integer"),
            ("F12", "Emails Per Hour", "integer"),
        ]

        return {
            "version": "1.0",
            "name": "F1-F12",
            "feature_count": 12,
            "features": [
                {
                    "feature_id": feature_id,
                    "name": name,
                    "data_type": data_type,
                }
                for feature_id, name, data_type in definitions
            ],
        }

    def _get_dataset_version_source_ids(
        self,
        dataset_id: UUID,
    ) -> list[UUID]:
        """
        Return the explicitly selected email IDs for a dataset.

        Versioning uses DatasetSample population, not the
        global eligible workspace population.
        """
        return self._deduplicate_ids(
            self.repository.list_dataset_email_ids(
                dataset_id=dataset_id,
            )
        )

    @staticmethod
    def _build_split_counts(
        memberships: Sequence[DatasetMembership],
    ) -> DatasetSplitCounts:
        counts = {
            "train": 0,
            "validation": 0,
            "test": 0,
        }

        for membership in memberships:
            split = str(
                getattr(
                    membership.split,
                    "value",
                    membership.split,
                )
            ).strip().lower()

            if split in counts:
                counts[split] += 1

        return DatasetSplitCounts(
            training=counts["train"],
            validation=counts["validation"],
            testing=counts["test"],
            total=sum(counts.values()),
        )

    @staticmethod
    def _build_split_configuration_from_version(
        version: DatasetVersion,
    ) -> DatasetSplitConfiguration:
        return DatasetSplitConfiguration(
            training_percentage=version.training_percentage,
            validation_percentage=version.validation_percentage,
            testing_percentage=version.testing_percentage,
            random_seed=version.random_seed,
            stratified=bool(version.stratified),
        )

    @staticmethod
    def _normalize_split(split: str) -> DatasetSplit:
        value = split.strip().lower()

        mapping = {
            "train": DatasetSplit.TRAIN,
            "training": DatasetSplit.TRAIN,
            "validation": DatasetSplit.VALIDATION,
            "valid": DatasetSplit.VALIDATION,
            "test": DatasetSplit.TEST,
            "testing": DatasetSplit.TEST,
        }

        if value not in mapping:
            raise DatasetValidationError(
                f"Unsupported split: {split}"
            )

        return mapping[value]

    @staticmethod
    def _record_to_dict(record: Any) -> dict[str, Any]:
        return {
            "email_id": str(record.email_id),
            "ground_truth": record.ground_truth,
            "f1_sender_email": record.f1_sender_email,
            "f2_known_domain": record.f2_known_domain,
            "f3_message_id": record.f3_message_id,
            "f4_auto_submitted": record.f4_auto_submitted,
            "f5_precedence_bulk": record.f5_precedence_bulk,
            "f6_list_id": record.f6_list_id,
            "f7_x_beenthere": record.f7_x_beenthere,
            "f8_x_anti_abuse": record.f8_x_anti_abuse,
            "f9_keyword_features": record.f9_keyword_features,
            "f10_subject_length": record.f10_subject_length,
            "f11_emails_per_minute": record.f11_emails_per_minute,
            "f12_emails_per_hour": record.f12_emails_per_hour,
            "split": record.split,
        }

    def _get_version_number_for_name(
        self,
        dataset_id: UUID,
        name: str,
    ) -> int:
        versions, _ = self.repository.list_dataset_versions(
            dataset_id=dataset_id,
            page=1,
            page_size=MAX_PAGE_SIZE,
        )

        matching = [
            version.version_number
            for version in versions
            if version.name == name.strip()
        ]

        if not matching:
            raise DatasetValidationError(
                "Could not resolve the newly created Dataset Version."
            )

        return max(matching)


# ============================================================
# FACTORY
# ============================================================

def create_dataset_service(
    repository: DatasetRepository,
) -> DatasetService:
    """Create a DatasetService instance."""
    return DatasetService(repository=repository)


__all__ = [
    "DatasetExportResult",
    "DatasetVersionCreationResult",
    "DatasetService",
    "create_dataset_service",
]