from __future__ import annotations

import time
from dataclasses import dataclass, field
from email import policy
from email.message import Message
from email.parser import BytesParser
from typing import Any

from .headers import extract_headers
from .normalizer import normalize_headers, normalize_text
from .validator import validate_parsed_email


@dataclass(slots=True)
class ParsedAttachment:
    """Metadata describing one MIME attachment."""

    filename: str | None
    content_type: str
    content_disposition: str | None
    size: int
    content_id: str | None = None


@dataclass(slots=True)
class ParsedMimePart:
    """Metadata describing one MIME part."""

    content_type: str
    content_disposition: str | None
    charset: str | None
    filename: str | None
    size: int


@dataclass(slots=True)
class ParsedEmail:
    """
    Complete in-memory representation produced by Module 03.

    This object is not a database model.

    Module 02 remains the canonical storage location for the
    original raw email.
    """

    message_id: str | None = None
    subject: str | None = None
    sender: str | None = None

    recipients: list[str] = field(default_factory=list)

    reply_to: list[str] = field(default_factory=list)
    cc: list[str] = field(default_factory=list)
    bcc: list[str] = field(default_factory=list)

    date: str | None = None

    headers: dict[str, list[str]] = field(
        default_factory=dict
    )

    text_body: str | None = None
    html_body: str | None = None

    mime_parts: list[ParsedMimePart] = field(
        default_factory=list
    )

    attachments: list[ParsedAttachment] = field(
        default_factory=list
    )

    validation_errors: list[str] = field(
        default_factory=list
    )

    validation_warnings: list[str] = field(
        default_factory=list
    )

    parser_version: str = "1.0.0"
    processing_time_ms: float = 0.0

    @property
    def is_valid(self) -> bool:
        """Return whether structural validation succeeded."""

        return not self.validation_errors


class EmailParser:
    """
    MIME parser for Module 03.

    Responsibilities:
    - Parse raw RFC/MIME email content.
    - Extract headers.
    - Extract addresses.
    - Extract text/plain and text/html bodies.
    - Discover MIME parts.
    - Collect attachment metadata.
    - Normalize extracted values.
    - Run structural validation.

    Responsibilities explicitly excluded:
    - ML feature extraction.
    - Bomb/normal classification.
    - Risk scoring.
    - Threat intelligence.
    - Detection decisions.
    """

    VERSION = "1.0.0"

    def parse(
        self,
        raw_content: str | bytes,
    ) -> ParsedEmail:
        """
        Parse one raw email.

        Parameters
        ----------
        raw_content:
            Raw RFC/MIME email content as text or bytes.

        Returns
        -------
        ParsedEmail
            Structured parsed representation.
        """

        started_at = time.perf_counter()

        raw_bytes = self._to_bytes(raw_content)

        message = BytesParser(
            policy=policy.default
        ).parsebytes(raw_bytes)

        parsed = self._parse_message(message)

        parsed.processing_time_ms = (
            time.perf_counter() - started_at
        ) * 1000

        return parsed

    # ============================================================
    # MESSAGE PARSING
    # ============================================================

    def _parse_message(
        self,
        message: Message,
    ) -> ParsedEmail:
        header_data = extract_headers(message)

        normalized_headers = normalize_headers(
            header_data["headers"]
        )

        parsed = ParsedEmail(
            message_id=header_data["message_id"],
            subject=header_data["subject"],
            sender=header_data["sender"],
            recipients=header_data["recipients"],
            reply_to=header_data["reply_to"],
            cc=header_data["cc"],
            bcc=header_data["bcc"],
            date=header_data["date"],
            headers=normalized_headers,
            parser_version=self.VERSION,
        )

        self._extract_parts(
            message=message,
            parsed=parsed,
        )

        self._normalize_bodies(parsed)

        validation = validate_parsed_email(parsed)

        parsed.validation_errors.extend(
            validation.errors
        )

        parsed.validation_warnings.extend(
            validation.warnings
        )

        return parsed

    # ============================================================
    # MIME PART EXTRACTION
    # ============================================================

    def _extract_parts(
        self,
        *,
        message: Message,
        parsed: ParsedEmail,
    ) -> None:
        """
        Walk the complete MIME tree.

        Multipart containers are recorded as MIME parts but do
        not themselves become message bodies.
        """

        for part in message.walk():
            content_type = part.get_content_type()
            disposition = part.get_content_disposition()
            filename = part.get_filename()
            charset = part.get_content_charset()

            payload = part.get_payload(decode=True)

            size = (
                len(payload)
                if isinstance(payload, bytes)
                else 0
            )

            parsed.mime_parts.append(
                ParsedMimePart(
                    content_type=content_type,
                    content_disposition=disposition,
                    charset=charset,
                    filename=filename,
                    size=size,
                )
            )

            if part.is_multipart():
                continue

            if disposition == "attachment" or filename:
                parsed.attachments.append(
                    self._build_attachment(part)
                )
                continue

            if content_type == "text/plain":
                body = self._get_part_content(part)

                if body:
                    parsed.text_body = self._merge_body(
                        parsed.text_body,
                        body,
                    )

            elif content_type == "text/html":
                body = self._get_part_content(part)

                if body:
                    parsed.html_body = self._merge_body(
                        parsed.html_body,
                        body,
                    )

    # ============================================================
    # ATTACHMENTS
    # ============================================================

    @staticmethod
    def _build_attachment(
        part: Message,
    ) -> ParsedAttachment:
        payload = part.get_payload(decode=True)

        size = (
            len(payload)
            if isinstance(payload, bytes)
            else 0
        )

        return ParsedAttachment(
            filename=part.get_filename(),
            content_type=part.get_content_type(),
            content_disposition=part.get_content_disposition(),
            size=size,
            content_id=part.get("Content-ID"),
        )

    # ============================================================
    # BODY DECODING
    # ============================================================

    @staticmethod
    def _get_part_content(
        part: Message,
    ) -> str | None:
        try:
            content = part.get_content()

            if isinstance(content, str):
                return content

        except (LookupError, UnicodeError):
            pass

        payload = part.get_payload(decode=True)

        if payload is None:
            return None

        charset = (
            part.get_content_charset()
            or "utf-8"
        )

        try:
            return payload.decode(
                charset,
                errors="replace",
            )
        except (LookupError, UnicodeError):
            return payload.decode(
                "utf-8",
                errors="replace",
            )

    # ============================================================
    # NORMALIZATION
    # ============================================================

    @staticmethod
    def _normalize_bodies(
        parsed: ParsedEmail,
    ) -> None:
        if parsed.text_body is not None:
            parsed.text_body = normalize_text(
                parsed.text_body
            )

        if parsed.html_body is not None:
            parsed.html_body = normalize_text(
                parsed.html_body
            )

    # ============================================================
    # HELPERS
    # ============================================================

    @staticmethod
    def _merge_body(
        current: str | None,
        new_content: str,
    ) -> str:
        if not current:
            return new_content

        return f"{current}\n\n{new_content}"

    @staticmethod
    def _to_bytes(
        raw_content: str | bytes,
    ) -> bytes:
        if isinstance(raw_content, bytes):
            return raw_content

        return raw_content.encode(
            "utf-8",
            errors="replace",
        )