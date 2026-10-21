"""Dashboard filter model and conversion to the existing Analytics contract."""

from datetime import datetime, timezone
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.modules.analytics.schemas import AnalyticsFilters


class DashboardFilters(BaseModel):
    """Filters accepted by all dashboard widgets.

    Date and model field names follow the Dashboard API proposal. Conversion
    below keeps the existing Analytics filter vocabulary at the integration
    boundary instead of duplicating its date and detection rules.
    """

    model_config = ConfigDict(extra="forbid")

    time_range: Literal["24h", "7d", "30d", "90d", "custom"] = "24h"
    classification: Literal["normal", "bomb"] | None = None
    risk_level: Literal["low", "medium", "high", "critical"] | None = None
    model_id: UUID | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None

    def to_analytics_filters(self) -> AnalyticsFilters:
        """Translate compatible filters to the established Analytics schema."""

        def utc(value: datetime | None) -> datetime | None:
            if value is None:
                return None
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value.astimezone(timezone.utc)

        return AnalyticsFilters(
            time_range=self.time_range,
            classification=self.classification,
            risk_level=self.risk_level,
            model_definition_id=self.model_id,
            from_date=utc(self.start_date),
            to_date=utc(self.end_date),
        )
