from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Iterable


# ============================================================
# TIME NORMALIZATION
# ============================================================

def normalize_datetime(value: datetime | None) -> datetime | None:
    """
    Normalize a datetime to timezone-aware UTC.

    Rules:
    - None remains None.
    - Timezone-aware values are converted to UTC.
    - Naive values are treated as UTC.

    Treating naive datetimes as UTC keeps the calculation
    deterministic when SQLite returns timestamps without
    timezone information.
    """

    if value is None:
        return None

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


# ============================================================
# TEMPORAL WINDOW
# ============================================================

def get_temporal_window(
    timestamp: datetime,
    window_seconds: int,
) -> tuple[datetime, datetime]:
    """
    Build an inclusive temporal window.

    Example:

        timestamp = T
        window_seconds = 60

        result:

            [T - 60 seconds, T]
    """

    if window_seconds < 0:
        raise ValueError("window_seconds must be non-negative")

    normalized_timestamp = normalize_datetime(timestamp)

    if normalized_timestamp is None:
        raise ValueError("timestamp is required")

    start = normalized_timestamp - timedelta(
        seconds=window_seconds,
    )

    return start, normalized_timestamp


# ============================================================
# EMAIL TIMESTAMP EXTRACTION
# ============================================================

def extract_received_timestamps(
    received_at_values: Iterable[datetime | None],
) -> list[datetime]:
    """
    Normalize a collection of received_at values.

    Invalid/missing timestamps are ignored.
    """

    timestamps: list[datetime] = []

    for value in received_at_values:
        normalized = normalize_datetime(value)

        if normalized is not None:
            timestamps.append(normalized)

    return timestamps


# ============================================================
# TEMPORAL COUNT
# ============================================================

def count_emails_in_window(
    received_at_values: Iterable[datetime | None],
    timestamp: datetime,
    window_seconds: int,
) -> int:
    """
    Count emails whose received_at timestamp falls inside
    the inclusive temporal window:

        [T - window_seconds, T]

    Both boundaries are included.

    The current email is therefore included when its
    received_at timestamp equals T.
    """

    start, end = get_temporal_window(
        timestamp=timestamp,
        window_seconds=window_seconds,
    )

    timestamps = extract_received_timestamps(
        received_at_values,
    )

    return sum(
        1
        for received_at in timestamps
        if start <= received_at <= end
    )


# ============================================================
# F11 — EMAILS PER MINUTE
# ============================================================

def calculate_emails_per_minute(
    received_at_values: Iterable[datetime | None],
    timestamp: datetime,
) -> int:
    """
    Calculate F11 — Emails Per Minute.

    Counts all collected emails whose received_at timestamp
    falls within:

        [T - 60 seconds, T]
    """

    return count_emails_in_window(
        received_at_values=received_at_values,
        timestamp=timestamp,
        window_seconds=60,
    )


# ============================================================
# F12 — EMAILS PER HOUR
# ============================================================

def calculate_emails_per_hour(
    received_at_values: Iterable[datetime | None],
    timestamp: datetime,
) -> int:
    """
    Calculate F12 — Emails Per Hour.

    Counts all collected emails whose received_at timestamp
    falls within:

        [T - 3600 seconds, T]
    """

    return count_emails_in_window(
        received_at_values=received_at_values,
        timestamp=timestamp,
        window_seconds=3600,
    )


# ============================================================
# F11 + F12
# ============================================================

def extract_temporal_features(
    received_at_values: Iterable[datetime | None],
    timestamp: datetime,
) -> dict[str, int]:
    """
    Extract temporal features F11 and F12.

    Returns:

        {
            "f11_emails_per_minute": <int>,
            "f12_emails_per_hour": <int>,
        }
    """

    return {
        "f11_emails_per_minute": calculate_emails_per_minute(
            received_at_values=received_at_values,
            timestamp=timestamp,
        ),
        "f12_emails_per_hour": calculate_emails_per_hour(
            received_at_values=received_at_values,
            timestamp=timestamp,
        ),
    }