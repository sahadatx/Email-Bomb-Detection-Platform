"""Dashboard-specific error vocabulary."""


class DashboardError(Exception):
    """Base exception for failures in dashboard aggregation."""


class DashboardSourceUnavailable(DashboardError):
    """A required source module could not provide its read-only data."""
