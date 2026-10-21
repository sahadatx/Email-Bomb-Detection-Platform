class AnalyticsError(Exception):
    """Base error for analytics requests."""


class InvalidAnalyticsFilter(AnalyticsError, ValueError):
    """Raised when an analytics filter is invalid."""
