"""Shared date window normalization, delegated to Analytics."""

from datetime import datetime, timezone

from app.modules.analytics.aggregations import date_window
from app.modules.analytics.errors import InvalidAnalyticsFilter
from ..selectors.dashboard_filters import DashboardFilters


def resolve_window(filters: DashboardFilters, *, now: datetime | None = None):
    """Validate custom date ranges and return an inclusive UTC time window."""
    normalized = filters
    if filters.time_range == "custom":
        if filters.start_date is None or filters.end_date is None:
            raise InvalidAnalyticsFilter(
                "Custom time range requires start_date and end_date."
            )
        start = filters.start_date
        end = filters.end_date
        start = start.replace(tzinfo=timezone.utc) if start.tzinfo is None else start
        end = end.replace(tzinfo=timezone.utc) if end.tzinfo is None else end
        start = start.astimezone(timezone.utc)
        end = end.astimezone(timezone.utc)
        if start > end:
            raise InvalidAnalyticsFilter(
                "start_date must be before or equal to end_date."
            )
        normalized = filters.model_copy(update={"start_date": start, "end_date": end})
    start, end = date_window(normalized.to_analytics_filters(), now=now)
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    return start.astimezone(timezone.utc), end.astimezone(timezone.utc)
