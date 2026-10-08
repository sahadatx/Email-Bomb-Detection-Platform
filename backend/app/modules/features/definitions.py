from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Final


class FeatureDataType(str, Enum):
    """Supported persisted feature data types."""

    STRING = "string"
    BOOLEAN = "boolean"
    INTEGER = "integer"
    FLOAT = "float"


class FeatureSource(str, Enum):
    """Canonical source of a feature value."""

    HEADER = "header"
    SENDER = "sender"
    SUBJECT = "subject"
    BODY = "body"
    TEMPORAL = "temporal"


@dataclass(frozen=True, slots=True)
class FeatureDefinition:
    """Immutable definition of one feature."""

    feature_id: str
    name: str
    description: str
    data_type: FeatureDataType
    source: FeatureSource
    calculation: str
    missing_value: str
    normalization: str


# ---------------------------------------------------------------------------
# F9 keyword contract
# ---------------------------------------------------------------------------

# These keywords are intentionally explicit and version-controlled.
# Matching is case-insensitive and performed against normalized text.
#
# The list is kept centralized so dataset generation, extraction,
# experiments, and thesis documentation can all refer to one contract.
SUSPICIOUS_KEYWORDS: Final[tuple[str, ...]] = (
    "confirm",
    "confirmation",
    "subscribe",
    "subscription",
    "newsletter",
    "unsubscribe",
    "verify",
    "verification",
    "activate",
    "activation",
    "update",
    "renew",
    "notification",
    "alert",
    "mailing",
    "promotional",
    "promotion",
    "bulk",
)


# ---------------------------------------------------------------------------
# F1–F12 definitions
# ---------------------------------------------------------------------------

FEATURE_DEFINITIONS: Final[tuple[FeatureDefinition, ...]] = (
    FeatureDefinition(
        feature_id="F1",
        name="Sender Email",
        description=(
            "Email address extracted from the parsed From header."
        ),
        data_type=FeatureDataType.STRING,
        source=FeatureSource.SENDER,
        calculation=(
            "Extract the normalized sender email address from the "
            "parsed sender identity."
        ),
        missing_value="Empty string when no valid sender address exists.",
        normalization="Trim whitespace and lowercase the email address.",
    ),
    FeatureDefinition(
        feature_id="F2",
        name="Known Domain Indicator",
        description=(
            "Indicates whether the sender domain belongs to the "
            "configured trusted-domain list."
        ),
        data_type=FeatureDataType.BOOLEAN,
        source=FeatureSource.SENDER,
        calculation=(
            "Extract the sender domain and return true when it exactly "
            "matches or is a valid subdomain of a configured trusted domain."
        ),
        missing_value="False when sender or sender domain is unavailable.",
        normalization="Lowercase and normalize the sender domain.",
    ),
    FeatureDefinition(
        feature_id="F3",
        name="Message-ID Presence",
        description=(
            "Indicates whether the email contains a valid Message-ID header."
        ),
        data_type=FeatureDataType.BOOLEAN,
        source=FeatureSource.HEADER,
        calculation=(
            "Return true when a non-empty Message-ID header exists and "
            "contains a syntactically valid message identifier."
        ),
        missing_value="False when Message-ID is missing or invalid.",
        normalization="Trim surrounding whitespace before validation.",
    ),
    FeatureDefinition(
        feature_id="F4",
        name="Auto-Submitted Header",
        description=(
            "Indicates whether the email contains an Auto-Submitted header."
        ),
        data_type=FeatureDataType.BOOLEAN,
        source=FeatureSource.HEADER,
        calculation=(
            "Return true when at least one non-empty Auto-Submitted "
            "header is present."
        ),
        missing_value="False when the header is absent.",
        normalization="Header name comparison is case-insensitive.",
    ),
    FeatureDefinition(
        feature_id="F5",
        name="Precedence Bulk Indicator",
        description=(
            "Indicates whether the email contains a Precedence header "
            "with a bulk-related value."
        ),
        data_type=FeatureDataType.BOOLEAN,
        source=FeatureSource.HEADER,
        calculation=(
            "Return true when the Precedence header contains the value "
            "'bulk' after case-insensitive normalization."
        ),
        missing_value="False when the header is absent or not bulk.",
        normalization="Trim and lowercase header values.",
    ),
    FeatureDefinition(
        feature_id="F6",
        name="List-Id Header",
        description=(
            "Indicates whether the email contains a List-Id header."
        ),
        data_type=FeatureDataType.BOOLEAN,
        source=FeatureSource.HEADER,
        calculation=(
            "Return true when at least one non-empty List-Id header exists."
        ),
        missing_value="False when the header is absent.",
        normalization="Header name comparison is case-insensitive.",
    ),
    FeatureDefinition(
        feature_id="F7",
        name="X-BeenThere Header",
        description=(
            "Indicates whether the email contains an X-BeenThere header."
        ),
        data_type=FeatureDataType.BOOLEAN,
        source=FeatureSource.HEADER,
        calculation=(
            "Return true when at least one non-empty X-BeenThere header exists."
        ),
        missing_value="False when the header is absent.",
        normalization="Header name comparison is case-insensitive.",
    ),
    FeatureDefinition(
        feature_id="F8",
        name="X-Anti-Abuse Header",
        description=(
            "Indicates whether the email contains an X-Anti-Abuse header."
        ),
        data_type=FeatureDataType.BOOLEAN,
        source=FeatureSource.HEADER,
        calculation=(
            "Return true when at least one non-empty X-Anti-Abuse "
            "header exists."
        ),
        missing_value="False when the header is absent.",
        normalization="Header name comparison is case-insensitive.",
    ),
    FeatureDefinition(
        feature_id="F9",
        name="Keyword-Based Content Features",
        description=(
            "Counts configured suspicious keyword occurrences in the "
            "normalized subject and text body."
        ),
        data_type=FeatureDataType.INTEGER,
        source=FeatureSource.BODY,
        calculation=(
            "Normalize subject and text body, tokenize case-insensitively, "
            "and count occurrences of configured suspicious keywords. "
            "The final value is the total number of keyword matches."
        ),
        missing_value="0 when subject and text body are both unavailable.",
        normalization=(
            "Unicode-aware lowercase matching with surrounding whitespace "
            "normalized. Matching is case-insensitive."
        ),
    ),
    FeatureDefinition(
        feature_id="F10",
        name="Subject Length",
        description=(
            "Number of characters in the normalized email subject."
        ),
        data_type=FeatureDataType.INTEGER,
        source=FeatureSource.SUBJECT,
        calculation=(
            "Trim the subject and return its character length."
        ),
        missing_value="0 when the subject is missing.",
        normalization="Trim leading/trailing whitespace.",
    ),
    FeatureDefinition(
        feature_id="F11",
        name="Emails Per Minute",
        description=(
            "Number of emails received within the one-minute temporal "
            "window ending at the current email's received timestamp."
        ),
        data_type=FeatureDataType.INTEGER,
        source=FeatureSource.TEMPORAL,
        calculation=(
            "For an email received at timestamp T, count collected emails "
            "with received_at in the inclusive interval [T - 60 seconds, T]."
        ),
        missing_value="0 when no usable received timestamp exists.",
        normalization="Timestamps are normalized to timezone-aware UTC.",
    ),
    FeatureDefinition(
        feature_id="F12",
        name="Emails Per Hour",
        description=(
            "Number of emails received within the one-hour temporal "
            "window ending at the current email's received timestamp."
        ),
        data_type=FeatureDataType.INTEGER,
        source=FeatureSource.TEMPORAL,
        calculation=(
            "For an email received at timestamp T, count collected emails "
            "with received_at in the inclusive interval [T - 3600 seconds, T]."
        ),
        missing_value="0 when no usable received timestamp exists.",
        normalization="Timestamps are normalized to timezone-aware UTC.",
    ),
)


FEATURE_IDS: Final[tuple[str, ...]] = tuple(
    definition.feature_id
    for definition in FEATURE_DEFINITIONS
)


FEATURE_DEFINITION_MAP: Final[dict[str, FeatureDefinition]] = {
    definition.feature_id: definition
    for definition in FEATURE_DEFINITIONS
}


FEATURE_COUNT: Final[int] = len(FEATURE_DEFINITIONS)


def get_feature_definition(feature_id: str) -> FeatureDefinition:
    """Return the definition for a feature ID."""

    normalized_id = feature_id.strip().upper()

    try:
        return FEATURE_DEFINITION_MAP[normalized_id]
    except KeyError as exc:
        raise ValueError(
            f"Unknown feature ID: {feature_id!r}"
        ) from exc


def get_all_feature_definitions() -> tuple[FeatureDefinition, ...]:
    """Return all feature definitions in canonical F1–F12 order."""

    return FEATURE_DEFINITIONS


def get_feature_ids() -> tuple[str, ...]:
    """Return canonical feature IDs."""

    return FEATURE_IDS


def is_valid_feature_id(feature_id: str) -> bool:
    """Return whether a feature ID belongs to the locked F1–F12 contract."""

    return feature_id.strip().upper() in FEATURE_DEFINITION_MAP