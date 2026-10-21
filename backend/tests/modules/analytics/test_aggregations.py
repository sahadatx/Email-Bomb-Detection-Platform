from datetime import datetime, timezone

import pytest

from app.modules.analytics.aggregations import date_window
from app.modules.analytics.errors import InvalidAnalyticsFilter
from app.modules.analytics.schemas import AnalyticsFilters


def test_custom_analytics_window_normalizes_naive_dates_to_utc():
    filters = AnalyticsFilters(
        time_range="custom",
        from_date=datetime(2026, 9, 1),
        to_date=datetime(2026, 9, 30, 23, 59),
    )

    start, end = date_window(filters)

    assert start.tzinfo == timezone.utc
    assert end.tzinfo == timezone.utc
    assert start < end


def test_custom_analytics_window_requires_both_dates():
    with pytest.raises(InvalidAnalyticsFilter):
        date_window(AnalyticsFilters(time_range="custom"))


def test_custom_analytics_window_rejects_reversed_dates():
    filters = AnalyticsFilters(
        time_range="custom",
        from_date=datetime(2026, 9, 30, tzinfo=timezone.utc),
        to_date=datetime(2026, 9, 1, tzinfo=timezone.utc),
    )

    with pytest.raises(InvalidAnalyticsFilter):
        date_window(filters)
