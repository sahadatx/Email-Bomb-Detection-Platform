from __future__ import annotations

from email.header import decode_header, make_header
from email.message import Message
from email.utils import getaddresses, parsedate_to_datetime


def extract_headers(
    message: Message,
) -> dict[str, object]:
    """
    Extract normalized high-level header information.

    This module handles:
    - Message-ID
    - Subject
    - From
    - To
    - Reply-To
    - Cc
    - Bcc
    - Date
    - Complete header collection
    """

    headers: dict[str, list[str]] = {}

    for name, value in message.items():
        headers.setdefault(
            name,
            [],
        ).append(
            _decode_header_value(value)
        )

    return {
        "headers": headers,
        "message_id": _clean_header(
            message.get("Message-ID")
        ),
        "subject": _decode_header_value(
            message.get("Subject")
        )
        if message.get("Subject") is not None
        else None,
        "sender": _extract_single_address(
            message.get("From")
        ),
        "recipients": _extract_addresses(
            message.get("To")
        ),
        "reply_to": _extract_addresses(
            message.get("Reply-To")
        ),
        "cc": _extract_addresses(
            message.get("Cc")
        ),
        "bcc": _extract_addresses(
            message.get("Bcc")
        ),
        "date": _normalize_date(
            message.get("Date")
        ),
    }


def _decode_header_value(
    value: str | None,
) -> str:
    """
    Decode RFC 2047 encoded header values safely.
    """

    if value is None:
        return ""

    try:
        return str(
            make_header(
                decode_header(value)
            )
        ).strip()

    except (UnicodeError, ValueError):
        return value.strip()


def _extract_addresses(
    value: str | None,
) -> list[str]:
    """
    Extract email addresses from a mailbox header.
    """

    if not value:
        return []

    addresses = getaddresses([value])

    return [
        address.strip()
        for _, address in addresses
        if address.strip()
    ]


def _extract_single_address(
    value: str | None,
) -> str | None:
    addresses = _extract_addresses(value)

    if not addresses:
        return None

    return addresses[0]


def _clean_header(
    value: str | None,
) -> str | None:
    if value is None:
        return None

    cleaned = value.strip()

    return cleaned or None


def _normalize_date(
    value: str | None,
) -> str | None:
    """
    Parse the RFC email Date header.

    The normalized output is ISO-8601 when parsing succeeds.
    The original decoded value is retained if parsing fails.
    """

    if not value:
        return None

    decoded = _decode_header_value(value)

    try:
        parsed = parsedate_to_datetime(decoded)

        if parsed is None:
            return decoded

        return parsed.isoformat()

    except (TypeError, ValueError, OverflowError):
        return decoded