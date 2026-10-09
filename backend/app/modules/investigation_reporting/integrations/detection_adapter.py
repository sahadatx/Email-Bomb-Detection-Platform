from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from ..repository import InvestigationRepository


class DetectionAdapter:
    """Translate persisted Module 08 detection rows to investigation payloads."""

    def __init__(self, db: Session) -> None:
        self.repository = InvestigationRepository(db)

    def get(self, detection_id: UUID) -> dict[str, Any] | None:
        return self.repository.get_detection(detection_id)

    def list(self, **filters: Any):
        return self.repository.list_detections(**filters)

    def exists(self, detection_id: UUID) -> bool:
        return self.repository.detection_exists(detection_id)

    def email_id(self, detection_id: UUID):
        payload = self.get(detection_id)
        return payload.get("email_id") if payload else None
