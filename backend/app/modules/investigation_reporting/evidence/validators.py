from __future__ import annotations

from typing import Any
from uuid import UUID

from ..errors import EvidenceValidationError


class EvidenceValidator:
    """Domain validation for source references, payload size and review transitions."""

    MAX_PROVENANCE_ITEMS = 100
    MAX_PROVENANCE_TEXT = 100_000

    def __init__(self, repository) -> None:
        self.repository = repository

    def validate_create(self, values: dict[str, Any]) -> None:
        detection_id = values.get("detection_id")
        if not detection_id or not self.repository.detection_exists(UUID(str(detection_id))):
            raise EvidenceValidationError("Related detection does not exist.")
        self._validate_email(values.get("source_email_id"))
        self._validate_detection_email(UUID(str(detection_id)), values.get("source_email_id"))
        self._validate_size(values)

    def validate_source_relationship(self, detection_id: UUID, source_email_id: UUID | None) -> None:
        if not self.repository.detection_exists(detection_id):
            raise EvidenceValidationError("Related detection does not exist.")
        self._validate_email(source_email_id)
        self._validate_detection_email(detection_id, source_email_id)

    def validate_update(self, evidence, values: dict[str, Any]) -> None:
        for field in ("name", "evidence_type"):
            if field in values and values[field] is None:
                raise EvidenceValidationError(f"Evidence {field.replace('_', ' ')} cannot be empty.")
        if "name" in values and not str(values["name"]).strip():
            raise EvidenceValidationError("Evidence name cannot be empty.")
        self._validate_email(values.get("source_email_id"))
        if values.get("source_email_id"):
            self._validate_detection_email(evidence.detection_id, values["source_email_id"])
        self._validate_size(values)

    def validate_review(self, current_status: str, values: dict[str, Any]) -> None:
        target = values.get("review_status")
        allowed = {"pending": {"pending", "verified", "flagged", "rejected"}, "flagged": {"pending", "verified", "flagged", "rejected"}, "rejected": {"pending", "rejected"}, "verified": {"pending", "verified"}}
        if target not in allowed.get(current_status, set()):
            raise EvidenceValidationError(f"Evidence cannot transition from '{current_status}' to '{target}'.")
        if not str(values.get("reason") or "").strip():
            raise EvidenceValidationError("A review reason is required.")

    def _validate_email(self, email_id) -> None:
        if email_id and not self.repository.email_exists(UUID(str(email_id))):
            raise EvidenceValidationError("Source email does not exist.")

    def _validate_detection_email(self, detection_id: UUID, email_id) -> None:
        if email_id:
            source_email_id = self.repository.detection_source_email(detection_id)
            if source_email_id != UUID(str(email_id)):
                raise EvidenceValidationError("Source email must match the email linked to this detection.")

    @classmethod
    def _validate_size(cls, values: dict[str, Any]) -> None:
        provenance = values.get("provenance")
        if provenance is not None:
            if not isinstance(provenance, dict) or len(provenance) > cls.MAX_PROVENANCE_ITEMS:
                raise EvidenceValidationError("Evidence provenance must be an object with at most 100 entries.")
            if len(str(provenance).encode("utf-8")) > cls.MAX_PROVENANCE_TEXT:
                raise EvidenceValidationError("Evidence provenance exceeds the 100 KB limit.")
