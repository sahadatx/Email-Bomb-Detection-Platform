from datetime import datetime, timedelta, timezone

from .errors import InvalidAnalyticsFilter


def date_window(filters, *, now=None):
    now = now or datetime.now(timezone.utc)
    if filters.time_range == "custom":
        if not filters.from_date or not filters.to_date:
            raise InvalidAnalyticsFilter("Custom time range requires from_date and to_date.")
        start, end = filters.from_date, filters.to_date
        if start > end:
            raise InvalidAnalyticsFilter("from_date must be before or equal to to_date.")
        if start.tzinfo is None: start = start.replace(tzinfo=timezone.utc)
        if end.tzinfo is None: end = end.replace(tzinfo=timezone.utc)
        return start.astimezone(timezone.utc), end.astimezone(timezone.utc)
    delta = {"24h": timedelta(hours=24), "7d": timedelta(days=7), "30d": timedelta(days=30), "90d": timedelta(days=90)}[filters.time_range]
    return now - delta, now


def chart_interval(start, end):
    return "hour" if end - start <= timedelta(days=2) else "day"
