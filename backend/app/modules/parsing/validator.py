from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .parser import ParsedEmail


@dataclass(slots=True)
class ValidationResult:
    """
    Result of structural and semantic email validation.
    """

    errors: list[str] = field(
        default_factory=list
    )

    warnings: list[str] = field(
        default_factory=list
    )

    @property
    def is_valid(self) -> bool:
        """
        Return True when no validation errors exist.
        """

        return not self.errors


def validate_parsed_email(
    parsed: ParsedEmail,
) -> ValidationResult:
    """
    Validate a parsed email.

    Validation is structural only.

    This function does NOT determine whether an email is:
    - malicious
    - spam
    - an email bomb
    - legitimate

    Those decisions belong to later modules.
    """

    result = ValidationResult()

    # ----------------------------------------------------------
    # Identity
    # ----------------------------------------------------------

    if not parsed.message_id:
        result.warnings.append(
            "Message-ID header is missing."
        )

    if not parsed.subject:
        result.warnings.append(
            "Subject header is missing."
        )

    # ----------------------------------------------------------
    # Sender
    # ----------------------------------------------------------

    if not parsed.sender:
        result.errors.append(
            "Sender address could not be extracted."
        )

    # ----------------------------------------------------------
    # Recipients
    # ----------------------------------------------------------

    if not parsed.recipients:
        result.warnings.append(
            "No To recipient was found."
        )

    # ----------------------------------------------------------
    # Content
    # ----------------------------------------------------------

    if (
        not parsed.text_body
        and not parsed.html_body
        and not parsed.attachments
    ):
        result.warnings.append(
            "No message body or attachment content was found."
        )

    # ----------------------------------------------------------
    # MIME structure
    # ----------------------------------------------------------

    if not parsed.mime_parts:
        result.errors.append(
            "No MIME parts were discovered."
        )

    # ----------------------------------------------------------
    # Attachment metadata
    # ----------------------------------------------------------

    for index, attachment in enumerate(
        parsed.attachments,
        start=1,
    ):
        if not attachment.content_type:
            result.warnings.append(
                f"Attachment {index} has no content type."
            )

        if attachment.size < 0:
            result.errors.append(
                f"Attachment {index} has an invalid size."
            )

    return result