from __future__ import annotations

import re
from collections import Counter
from typing import Final, Iterable

from app.modules.features.definitions import SUSPICIOUS_KEYWORDS


# ============================================================
# NORMALIZATION
# ============================================================

_WHITESPACE_RE: Final[re.Pattern[str]] = re.compile(r"\s+")


def normalize_content(value: str | None) -> str:
    """
    Normalize textual content for deterministic feature extraction.

    Rules:
    - Missing values become an empty string.
    - Normalize Unicode-compatible whitespace through Python's
      standard string handling.
    - Collapse consecutive whitespace.
    - Strip leading/trailing whitespace.
    """

    if value is None:
        return ""

    return _WHITESPACE_RE.sub(" ", value).strip()


def normalize_subject(subject: str | None) -> str:
    """
    Normalize an email subject before calculating F10.
    """

    return normalize_content(subject)


# ============================================================
# F10 — SUBJECT LENGTH
# ============================================================

def calculate_subject_length(
    subject: str | None,
) -> int:
    """
    Calculate F10 — Subject Length.

    The value is the number of characters in the normalized
    subject.

    Missing subject -> 0.
    """

    normalized_subject = normalize_subject(subject)

    return len(normalized_subject)


# ============================================================
# KEYWORD NORMALIZATION
# ============================================================

def normalize_keywords(
    keywords: Iterable[str],
) -> tuple[str, ...]:
    """
    Normalize and deduplicate the configured keyword list.

    Keyword matching is case-insensitive.
    Empty keywords are ignored.
    """

    normalized: set[str] = set()

    for keyword in keywords:
        if not isinstance(keyword, str):
            continue

        value = normalize_content(keyword).casefold()

        if value:
            normalized.add(value)

    return tuple(sorted(normalized))


# ============================================================
# TOKENIZATION
# ============================================================

_WORD_RE: Final[re.Pattern[str]] = re.compile(
    r"[^\W_]+(?:['-][^\W_]+)*",
    flags=re.UNICODE,
)


def tokenize_content(
    value: str | None,
) -> list[str]:
    """
    Tokenize normalized textual content.

    Tokens are case-folded for deterministic case-insensitive
    keyword matching.
    """

    normalized = normalize_content(value)

    if not normalized:
        return []

    return [
        token.casefold()
        for token in _WORD_RE.findall(normalized)
    ]


# ============================================================
# F9 — KEYWORD-BASED CONTENT FEATURES
# ============================================================

def count_keyword_occurrences(
    text: str | None,
    keywords: Iterable[str] = SUSPICIOUS_KEYWORDS,
) -> int:
    """
    Count total occurrences of configured keywords.

    Matching is:
    - case-insensitive
    - token-based
    - deterministic

    Example:

        text:
            "Confirm your subscription. Confirm now."

        keyword:
            "confirm"

        result:
            2
    """

    tokens = tokenize_content(text)

    if not tokens:
        return 0

    normalized_keywords = set(
        normalize_keywords(keywords)
    )

    if not normalized_keywords:
        return 0

    return sum(
        1
        for token in tokens
        if token in normalized_keywords
    )


def count_keyword_matches(
    subject: str | None,
    text_body: str | None,
    keywords: Iterable[str] = SUSPICIOUS_KEYWORDS,
) -> int:
    """
    Calculate F9 from both normalized subject and text body.

    The final value is the total number of keyword occurrences
    across both sources.
    """

    subject_count = count_keyword_occurrences(
        subject,
        keywords,
    )

    body_count = count_keyword_occurrences(
        text_body,
        keywords,
    )

    return subject_count + body_count


def get_keyword_match_details(
    subject: str | None,
    text_body: str | None,
    keywords: Iterable[str] = SUSPICIOUS_KEYWORDS,
) -> dict[str, int]:
    """
    Return per-keyword occurrence counts.

    This is supporting evidence for F9 and does not create
    additional ML features.
    """

    normalized_keywords = normalize_keywords(keywords)

    if not normalized_keywords:
        return {}

    combined_text = " ".join(
        part
        for part in (
            normalize_content(subject),
            normalize_content(text_body),
        )
        if part
    )

    tokens = tokenize_content(combined_text)

    counts = Counter(
        token
        for token in tokens
        if token in normalized_keywords
    )

    return {
        keyword: counts.get(keyword, 0)
        for keyword in normalized_keywords
    }


# ============================================================
# F9 + F10
# ============================================================

def extract_content_features(
    subject: str | None,
    text_body: str | None,
    keywords: Iterable[str] = SUSPICIOUS_KEYWORDS,
) -> dict[str, int]:
    """
    Extract content-related features F9 and F10.

    Returns:

        {
            "f9_keyword_features": <int>,
            "f10_subject_length": <int>,
        }
    """

    return {
        "f9_keyword_features": count_keyword_matches(
            subject=subject,
            text_body=text_body,
            keywords=keywords,
        ),
        "f10_subject_length": calculate_subject_length(
            subject,
        ),
    }