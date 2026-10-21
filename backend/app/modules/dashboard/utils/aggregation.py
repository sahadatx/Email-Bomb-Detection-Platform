"""Normalize existing analytics payloads into the Dashboard response contract."""

from typing import Any


def distribution_map(rows: list[dict[str, Any]], key: str, values: tuple[str, ...]):
    """Return a complete zero-filled distribution without fabricating data."""
    counts = {value: 0 for value in values}
    for row in rows:
        label = row.get(key)
        if label in counts:
            counts[label] += int(row.get("count", 0))
    return [{key: label, "count": count} for label, count in counts.items()]


def normalize_trend(rows: list[dict[str, Any]]):
    """Keep only the public chart fields and ensure numeric values are integers."""
    return [
        {
            "timestamp": str(row["timestamp"]),
            "normal": int(row.get("normal", 0)),
            "bomb": int(row.get("bomb", 0)),
        }
        for row in rows
    ]
