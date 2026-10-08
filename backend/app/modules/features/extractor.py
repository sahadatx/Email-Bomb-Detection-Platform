from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from time import perf_counter
from typing import Iterable, Mapping, Sequence


from app.modules.features.content import (
    extract_content_features,
)
from app.modules.features.definitions import (
    FEATURE_COUNT,
    get_feature_ids,
)
from app.modules.features.sender import (
    extract_sender_features,
)
from app.modules.features.temporal import (
    extract_temporal_features,
)


# ============================================================
# EXTRACTOR VERSION
# ============================================================

EXTRACTOR_VERSION = "1.0.0"


# ============================================================
# INPUT MODEL
# ============================================================


@dataclass(frozen=True, slots=True)
class ParsedEmailInput:
    """
    Normalized email representation required by Module 04.

    Module 04 consumes parsed/normalized email information.

    This object intentionally excludes:

        - prediction
        - classification
        - confidence
        - risk score
        - threat score
        - threat level

    Feature Engineering is responsible only for deterministic
    F1-F12 feature extraction.
    """

    # --------------------------------------------------------
    # Module 02 canonical email information
    # --------------------------------------------------------

    sender: str | None = None
    subject: str | None = None
    message_id: str | None = None

    received_at: datetime | None = None

    # --------------------------------------------------------
    # Module 03 parsed header information
    # --------------------------------------------------------

    auto_submitted: str | None = None
    precedence: str | None = None
    list_id: str | None = None
    x_beenthere: str | None = None
    x_anti_abuse: str | None = None

    # --------------------------------------------------------
    # Module 03 normalized body
    # --------------------------------------------------------

    text_body: str | None = None

    # --------------------------------------------------------
    # Complete collected-email timestamp population.
    #
    # Required by:
    #
    #     F11 — Emails Per Minute
    #     F12 — Emails Per Hour
    # --------------------------------------------------------

    all_received_at: Sequence[
        datetime | None
    ] = field(
        default_factory=tuple,
    )


# ============================================================
# EXTRACTION RESULT
# ============================================================


@dataclass(frozen=True, slots=True)
class FeatureExtractionResult:
    """
    Complete deterministic F1-F12 extraction result.

    feature_vector
        Canonical F1-F12 representation.

    errors
        Fatal validation/extraction errors.

    warnings
        Non-fatal extraction warnings.

    processing_time_ms
        Total extractor execution time.
    """

    feature_vector: dict[str, object]

    errors: list[str]

    warnings: list[str]

    processing_time_ms: int

    extractor_version: str = EXTRACTOR_VERSION

    @property
    def is_valid(self) -> bool:
        """
        Return True when no extraction errors exist.
        """

        return not self.errors

    @property
    def feature_count(self) -> int:
        """
        Return the number of generated feature IDs.
        """

        return len(
            self.feature_vector,
        )


# ============================================================
# NORMALIZATION HELPERS
# ============================================================


def _normalize_header_value(
    value: str | None,
) -> str | None:
    """
    Normalize a parsed header value.

    Header presence features only require determining whether
    a meaningful header value exists.

    Therefore surrounding whitespace is removed and empty
    values become None.
    """

    if value is None:
        return None

    normalized = value.strip()

    if not normalized:
        return None

    return normalized


def _build_header_mapping(
    email: ParsedEmailInput,
) -> Mapping[str, str | None]:
    """
    Build the canonical header mapping used by F3-F8.
    """

    return {
        "message_id": _normalize_header_value(
            email.message_id,
        ),
        "auto_submitted": _normalize_header_value(
            email.auto_submitted,
        ),
        "precedence": _normalize_header_value(
            email.precedence,
        ),
        "list_id": _normalize_header_value(
            email.list_id,
        ),
        "x_beenthere": _normalize_header_value(
            email.x_beenthere,
        ),
        "x_anti_abuse": _normalize_header_value(
            email.x_anti_abuse,
        ),
    }


# ============================================================
# MESSAGE-ID VALIDATION
# ============================================================


def _is_valid_message_id(
    value: str | None,
) -> bool:
    """
    Perform lightweight Message-ID validation.

    Expected general structure:

        <local-part@domain>

    This intentionally does not implement complete RFC
    Message-ID parsing.

    Full email/header parsing belongs to Module 03.
    """

    if not value:
        return False

    normalized = value.strip()

    if len(normalized) < 5:
        return False

    if not normalized.startswith("<"):
        return False

    if not normalized.endswith(">"):
        return False

    inner = normalized[1:-1].strip()

    if not inner:
        return False

    if inner.count("@") != 1:
        return False

    local_part, domain = inner.rsplit(
        "@",
        1,
    )

    if not local_part:
        return False

    if not domain:
        return False

    if " " in inner:
        return False

    if "." not in domain:
        return False

    return True


# ============================================================
# PRECEDENCE / BULK DETECTION
# ============================================================


def _contains_bulk(
    value: str | None,
) -> bool:
    """
    Determine whether the Precedence header contains the
    'bulk' token.

    Matching is case-insensitive.

    Supported examples include:

        bulk
        BULK
        list, bulk
        junk bulk
    """

    if not value:
        return False

    normalized = value.casefold()

    # --------------------------------------------------------
    # Comma-separated header values
    # --------------------------------------------------------

    comma_tokens = {
        token.strip()
        for token in normalized.split(",")
        if token.strip()
    }

    if "bulk" in comma_tokens:
        return True

    # --------------------------------------------------------
    # Whitespace-separated values
    # --------------------------------------------------------

    whitespace_tokens = {
        token.strip(" ;")
        for token in normalized.split()
        if token.strip(" ;")
    }

    return "bulk" in whitespace_tokens


# ============================================================
# F3-F8 HEADER FEATURES
# ============================================================


def _extract_header_features(
    email: ParsedEmailInput,
) -> dict[str, bool]:
    """
    Extract F3-F8 from normalized header values.

    F3
        Message-ID Presence

    F4
        Auto-Submitted Header

    F5
        Precedence Bulk Indicator

    F6
        List-Id Header

    F7
        X-BeenThere Header

    F8
        X-Anti-Abuse Header
    """

    headers = _build_header_mapping(
        email,
    )

    message_id = headers[
        "message_id"
    ]

    auto_submitted = headers[
        "auto_submitted"
    ]

    precedence = headers[
        "precedence"
    ]

    list_id = headers[
        "list_id"
    ]

    x_beenthere = headers[
        "x_beenthere"
    ]

    x_anti_abuse = headers[
        "x_anti_abuse"
    ]

    return {
        "f3_message_id": _is_valid_message_id(
            message_id,
        ),
        "f4_auto_submitted": bool(
            auto_submitted,
        ),
        "f5_precedence_bulk": _contains_bulk(
            precedence,
        ),
        "f6_list_id": bool(
            list_id,
        ),
        "f7_x_beenthere": bool(
            x_beenthere,
        ),
        "f8_x_anti_abuse": bool(
            x_anti_abuse,
        ),
    }


# ============================================================
# FEATURE VECTOR VALIDATION
# ============================================================


def validate_feature_vector(
    feature_vector: Mapping[str, object],
) -> tuple[list[str], list[str]]:
    """
    Validate the completed canonical F1-F12 feature vector.

    Returns:

        (
            validation_errors,
            validation_warnings,
        )

    Expected vector:

        F1  string | None
        F2  bool
        F3  bool
        F4  bool
        F5  bool
        F6  bool
        F7  bool
        F8  bool
        F9  int
        F10 int
        F11 int
        F12 int
    """

    errors: list[str] = []
    warnings: list[str] = []

    expected_ids = set(
        get_feature_ids(),
    )

    actual_ids = set(
        feature_vector.keys(),
    )

    # --------------------------------------------------------
    # Missing features
    # --------------------------------------------------------

    missing = expected_ids - actual_ids

    if missing:
        errors.append(
            "Missing feature IDs: "
            + ", ".join(
                sorted(missing),
            )
        )

    # --------------------------------------------------------
    # Unexpected features
    # --------------------------------------------------------

    unexpected = actual_ids - expected_ids

    if unexpected:
        errors.append(
            "Unexpected feature IDs: "
            + ", ".join(
                sorted(unexpected),
            )
        )

    # --------------------------------------------------------
    # Feature count
    # --------------------------------------------------------

    if len(feature_vector) != FEATURE_COUNT:
        errors.append(
            f"Expected {FEATURE_COUNT} features, "
            f"got {len(feature_vector)}."
        )

    # --------------------------------------------------------
    # F1 — Sender Email
    # --------------------------------------------------------

    if "F1" in feature_vector:
        value = feature_vector["F1"]

        if value is not None and not isinstance(
            value,
            str,
        ):
            errors.append(
                "F1 must be a string or None.",
            )

    # --------------------------------------------------------
    # F2-F8 — Boolean features
    # --------------------------------------------------------

    for feature_id in (
        "F2",
        "F3",
        "F4",
        "F5",
        "F6",
        "F7",
        "F8",
    ):
        if feature_id not in feature_vector:
            continue

        value = feature_vector[
            feature_id
        ]

        if not isinstance(
            value,
            bool,
        ):
            errors.append(
                f"{feature_id} must be boolean.",
            )

    # --------------------------------------------------------
    # F9-F12 — Integer features
    # --------------------------------------------------------

    for feature_id in (
        "F9",
        "F10",
        "F11",
        "F12",
    ):
        if feature_id not in feature_vector:
            continue

        value = feature_vector[
            feature_id
        ]

        # bool is a subclass of int in Python.
        if (
            not isinstance(
                value,
                int,
            )
            or isinstance(
                value,
                bool,
            )
        ):
            errors.append(
                f"{feature_id} must be an integer.",
            )
            continue

        if value < 0:
            errors.append(
                f"{feature_id} cannot be negative.",
            )

    return errors, warnings


# ============================================================
# CANONICAL VECTOR BUILDER
# ============================================================


def _build_feature_vector(
    sender_features: Mapping[str, object],
    header_features: Mapping[str, object],
    content_features: Mapping[str, object],
    temporal_features: Mapping[str, object],
) -> dict[str, object]:
    """
    Build the canonical F1-F12 vector.

    The returned keys are intentionally exactly:

        F1 ... F12
    """

    return {
        # ----------------------------------------------------
        # Sender
        # ----------------------------------------------------

        "F1": sender_features.get(
            "f1_sender_email",
        ),
        "F2": sender_features.get(
            "f2_known_domain",
            False,
        ),

        # ----------------------------------------------------
        # Headers
        # ----------------------------------------------------

        "F3": header_features.get(
            "f3_message_id",
            False,
        ),
        "F4": header_features.get(
            "f4_auto_submitted",
            False,
        ),
        "F5": header_features.get(
            "f5_precedence_bulk",
            False,
        ),
        "F6": header_features.get(
            "f6_list_id",
            False,
        ),
        "F7": header_features.get(
            "f7_x_beenthere",
            False,
        ),
        "F8": header_features.get(
            "f8_x_anti_abuse",
            False,
        ),

        # ----------------------------------------------------
        # Content
        # ----------------------------------------------------

        "F9": content_features.get(
            "f9_keyword_features",
            0,
        ),
        "F10": content_features.get(
            "f10_subject_length",
            0,
        ),

        # ----------------------------------------------------
        # Temporal
        # ----------------------------------------------------

        "F11": temporal_features.get(
            "f11_emails_per_minute",
            0,
        ),
        "F12": temporal_features.get(
            "f12_emails_per_hour",
            0,
        ),
    }


# ============================================================
# EXTRACTION FAILURE RESULT
# ============================================================


def _build_failure_result(
    *,
    error: str,
    started_at: float,
) -> FeatureExtractionResult:
    """
    Build a consistent extraction failure result.
    """

    processing_time_ms = max(
        0,
        round(
            (
                perf_counter()
                - started_at
            )
            * 1000
        ),
    )

    return FeatureExtractionResult(
        feature_vector={},
        errors=[error],
        warnings=[],
        processing_time_ms=processing_time_ms,
        extractor_version=EXTRACTOR_VERSION,
    )


# ============================================================
# F1-F12 ORCHESTRATOR
# ============================================================


def extract_features(
    email: ParsedEmailInput,
    trusted_domains: Iterable[str] | None = None,
) -> FeatureExtractionResult:
    """
    Extract the complete deterministic F1-F12 feature vector.

    Pipeline:

        ParsedEmailInput
              │
              ├── F1-F2   → sender.py
              │
              ├── F3-F8   → header extraction
              │
              ├── F9-F10  → content.py
              │
              └── F11-F12 → temporal.py
              │
              ▼
        Canonical F1-F12 vector
              │
              ▼
        Vector validation
              │
              ▼
        FeatureExtractionResult

    This function performs orchestration only.

    It does not:
        - access the database
        - perform ML
        - classify emails
        - calculate risk
        - calculate threat scores
        - generate predictions
    """

    started_at = perf_counter()

    errors: list[str] = []
    warnings: list[str] = []

    try:
        # ====================================================
        # F1-F2 — SENDER
        # ====================================================

        sender_features = (
            extract_sender_features(
                sender=email.sender,
                trusted_domains=trusted_domains,
            )
        )

        # ====================================================
        # F3-F8 — HEADERS
        # ====================================================

        header_features = (
            _extract_header_features(
                email,
            )
        )

        # ====================================================
        # F9-F10 — CONTENT
        # ====================================================

        content_features = (
            extract_content_features(
                subject=email.subject,
                text_body=email.text_body,
            )
        )

        # ====================================================
        # F11-F12 — TEMPORAL
        # ====================================================

        if email.received_at is None:
            temporal_features = {
                "f11_emails_per_minute": 0,
                "f12_emails_per_hour": 0,
            }

            warnings.append(
                "received_at is missing; "
                "F11 and F12 defaulted to 0.",
            )

        else:
            temporal_features = (
                extract_temporal_features(
                    received_at_values=(
                        email.all_received_at
                    ),
                    timestamp=email.received_at,
                )
            )

        # ====================================================
        # BUILD CANONICAL VECTOR
        # ====================================================

        feature_vector = _build_feature_vector(
            sender_features=sender_features,
            header_features=header_features,
            content_features=content_features,
            temporal_features=temporal_features,
        )

        # ====================================================
        # VALIDATE VECTOR
        # ====================================================

        validation_errors, validation_warnings = (
            validate_feature_vector(
                feature_vector,
            )
        )

        errors.extend(
            validation_errors,
        )

        warnings.extend(
            validation_warnings,
        )

    except Exception as exc:
        return _build_failure_result(
            error=(
                "Feature extraction failed: "
                f"{exc}"
            ),
            started_at=started_at,
        )

    # ========================================================
    # PROCESSING TIME
    # ========================================================

    processing_time_ms = max(
        0,
        round(
            (
                perf_counter()
                - started_at
            )
            * 1000
        ),
    )

    # ========================================================
    # RESULT
    # ========================================================

    return FeatureExtractionResult(
        feature_vector=feature_vector,
        errors=errors,
        warnings=warnings,
        processing_time_ms=processing_time_ms,
        extractor_version=EXTRACTOR_VERSION,
    )


# ============================================================
# CONVENIENCE API
# ============================================================


def extract_feature_vector(
    email: ParsedEmailInput,
    trusted_domains: Iterable[str] | None = None,
) -> dict[str, object]:
    """
    Extract and return only the canonical F1-F12 vector.

    Raises:
        ValueError
            When extraction or vector validation fails.
    """

    result = extract_features(
        email=email,
        trusted_domains=trusted_domains,
    )

    if result.errors:
        raise ValueError(
            "; ".join(
                result.errors,
            ),
        )

    return result.feature_vector


# ============================================================
# EXTRACTOR METADATA
# ============================================================


def get_extractor_version() -> str:
    """
    Return the currently active extractor version.
    """

    return EXTRACTOR_VERSION


def get_expected_feature_count() -> int:
    """
    Return the expected F1-F12 feature count.
    """

    return FEATURE_COUNT


def get_expected_feature_ids() -> tuple[str, ...]:
    """
    Return the canonical ordered feature IDs.
    """

    return tuple(
        get_feature_ids(),
    )