from __future__ import annotations

import re
import unicodedata


_WHITESPACE_RE = re.compile(
    r"[ \t]+"
)

_NEWLINE_RE = re.compile(
    r"\n{3,}"
)


def normalize_text(
    value: str,
) -> str:
    """
    Normalize textual email content without destroying
    meaningful content.

    Operations:
    - Unicode normalization.
    - CRLF/CR → LF.
    - Trailing whitespace cleanup.
    - Excessive blank-line reduction.

    HTML markup is intentionally preserved.
    """

    if not value:
        return ""

    normalized = unicodedata.normalize(
        "NFC",
        value,
    )

    normalized = normalized.replace(
        "\r\n",
        "\n",
    ).replace(
        "\r",
        "\n",
    )

    normalized = "\n".join(
        line.rstrip()
        for line in normalized.split("\n")
    )

    normalized = _NEWLINE_RE.sub(
        "\n\n",
        normalized,
    )

    return normalized.strip()


def normalize_headers(
    headers: dict[str, list[str]],
) -> dict[str, list[str]]:
    """
    Normalize header names and header values.

    Header names are represented case-insensitively using their
    lowercase form.

    Duplicate header values are preserved.
    """

    normalized: dict[str, list[str]] = {}

    for name, values in headers.items():
        normalized_name = name.strip().lower()

        if not normalized_name:
            continue

        normalized_values = [
            normalize_header_value(value)
            for value in values
        ]

        normalized[normalized_name] = (
            normalized_values
        )

    return normalized


def normalize_header_value(
    value: str,
) -> str:
    """
    Normalize one header value while preserving its meaning.
    """

    if not value:
        return ""

    normalized = unicodedata.normalize(
        "NFC",
        value,
    )

    normalized = normalized.replace(
        "\r\n",
        "\n",
    ).replace(
        "\r",
        "\n",
    )

    lines = [
        _WHITESPACE_RE.sub(
            " ",
            line.strip(),
        )
        for line in normalized.split("\n")
    ]

    return " ".join(
        line
        for line in lines
        if line
    ).strip()