from __future__ import annotations

import hashlib

from dataclasses import dataclass
from datetime import datetime
from email import policy
from email.parser import Parser
from email.utils import parsedate_to_datetime
from typing import BinaryIO


@dataclass(frozen=True)
class CollectedEmail:
    """Normalized ingestion-level representation of a raw email."""

    raw_content: str
    content_hash: str

    message_id: str | None
    sender: str | None
    recipients: str | None

    cc: str | None
    bcc: str | None
    reply_to: str | None

    subject: str | None

    content_type: str | None
    mime_version: str | None

    received_at: datetime | None


class EmailCollector:
    """
    Collect raw email data and extract ingestion-level metadata.

    This component is intentionally limited to ingestion-level
    normalization and metadata extraction.

    Full email parsing, normalization, and feature extraction
    belong to later modules.
    """

    def collect_text(
        self,
        raw_content: str,
    ) -> CollectedEmail:
        """
        Collect and normalize an email supplied as text.

        Args:
            raw_content: Complete raw RFC email content.

        Returns:
            A normalized CollectedEmail instance.

        Raises:
            ValueError: If the email content is empty.
        """

        if not raw_content or not raw_content.strip():
            raise ValueError(
                "Email content cannot be empty."
            )

        normalized = (
            raw_content
            .replace("\r\n", "\n")
            .replace("\r", "\n")
        )

        content_hash = hashlib.sha256(
            normalized.encode("utf-8")
        ).hexdigest()

        message = Parser(
            policy=policy.default
        ).parsestr(normalized)

        return CollectedEmail(
            raw_content=normalized,
            content_hash=content_hash,

            message_id=self._clean_header(
                message.get("Message-ID")
            ),

            sender=self._clean_header(
                message.get("From")
            ),

            recipients=self._clean_header(
                message.get("To")
            ),

            cc=self._clean_header(
                message.get("Cc")
            ),

            bcc=self._clean_header(
                message.get("Bcc")
            ),

            reply_to=self._clean_header(
                message.get("Reply-To")
            ),

            subject=self._clean_header(
                message.get("Subject")
            ),

            content_type=self._clean_header(
                message.get("Content-Type")
            ),

            mime_version=self._clean_header(
                message.get("MIME-Version")
            ),

            received_at=self._parse_date(
                message.get("Date")
            ),
        )

    def collect_bytes(
        self,
        raw_data: bytes,
    ) -> CollectedEmail:
        """
        Collect an email supplied as raw bytes.
        """

        if not raw_data:
            raise ValueError(
                "Email content cannot be empty."
            )

        raw_content = raw_data.decode(
            "utf-8",
            errors="replace",
        )

        return self.collect_text(
            raw_content
        )

    def collect_file(
        self,
        file: BinaryIO,
    ) -> CollectedEmail:
        """
        Collect an email from a binary file-like object.
        """

        raw_data = file.read()

        if not isinstance(raw_data, bytes):
            raise ValueError(
                "Email file must provide binary content."
            )

        return self.collect_bytes(
            raw_data
        )

    @staticmethod
    def _clean_header(
        value: str | None,
    ) -> str | None:
        """
        Normalize an optional email header value.

        Empty or whitespace-only values are converted to None.
        """

        if value is None:
            return None

        normalized = str(value).strip()

        return normalized or None

    @staticmethod
    def _parse_date(
        value: str | None,
    ) -> datetime | None:
        """
        Parse the email Date header.
        """

        if not value:
            return None

        try:
            return parsedate_to_datetime(value)
        except (
            TypeError,
            ValueError,
            IndexError,
        ):
            return None