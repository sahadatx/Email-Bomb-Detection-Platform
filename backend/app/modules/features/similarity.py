from __future__ import annotations

import re
from collections import Counter
from math import sqrt


_WHITESPACE_RE = re.compile(r"\s+")


def normalize_text(value: str | None) -> str:
    """
    Normalize text for deterministic similarity comparison.

    Rules:
    - None -> empty string
    - lowercase/casefold
    - collapse consecutive whitespace
    - strip leading/trailing whitespace
    """

    if value is None:
        return ""

    normalized = value.casefold()
    normalized = _WHITESPACE_RE.sub(" ", normalized)

    return normalized.strip()


def tokenize(value: str | None) -> list[str]:
    """
    Convert text into normalized whitespace-separated tokens.
    """

    normalized = normalize_text(value)

    if not normalized:
        return []

    return normalized.split()


def build_token_frequency(
    value: str | None,
) -> Counter[str]:
    """
    Build a token-frequency representation of text.
    """

    return Counter(tokenize(value))


def calculate_cosine_similarity(
    first: str | None,
    second: str | None,
) -> float:
    """
    Calculate cosine similarity between two text values.

    Returns a value in the range:

        0.0 -> completely different / no shared tokens
        1.0 -> identical token-frequency vectors

    This is a deterministic helper and is not an ML prediction.
    """

    first_vector = build_token_frequency(first)
    second_vector = build_token_frequency(second)

    if not first_vector or not second_vector:
        return 0.0

    common_tokens = set(first_vector) & set(second_vector)

    dot_product = sum(
        first_vector[token] * second_vector[token]
        for token in common_tokens
    )

    first_norm = sqrt(
        sum(
            value * value
            for value in first_vector.values()
        )
    )

    second_norm = sqrt(
        sum(
            value * value
            for value in second_vector.values()
        )
    )

    if first_norm == 0.0 or second_norm == 0.0:
        return 0.0

    similarity = dot_product / (
        first_norm * second_norm
    )

    # Protect against floating-point drift.
    return max(0.0, min(1.0, similarity))


def calculate_jaccard_similarity(
    first: str | None,
    second: str | None,
) -> float:
    """
    Calculate token-set Jaccard similarity.

    Returns a value in the range [0.0, 1.0].
    """

    first_tokens = set(tokenize(first))
    second_tokens = set(tokenize(second))

    if not first_tokens and not second_tokens:
        return 1.0

    if not first_tokens or not second_tokens:
        return 0.0

    intersection = first_tokens & second_tokens
    union = first_tokens | second_tokens

    if not union:
        return 0.0

    return len(intersection) / len(union)


def is_similar(
    first: str | None,
    second: str | None,
    threshold: float = 0.80,
) -> bool:
    """
    Determine whether two texts meet the supplied similarity
    threshold using cosine similarity.

    Threshold must be between 0.0 and 1.0.
    """

    if not 0.0 <= threshold <= 1.0:
        raise ValueError(
            "threshold must be between 0.0 and 1.0"
        )

    return (
        calculate_cosine_similarity(first, second)
        >= threshold
    )


def calculate_subject_similarity(
    first_subject: str | None,
    second_subject: str | None,
) -> float:
    """
    Convenience helper for comparing two email subjects.
    """

    return calculate_cosine_similarity(
        first_subject,
        second_subject,
    )


def calculate_body_similarity(
    first_body: str | None,
    second_body: str | None,
) -> float:
    """
    Convenience helper for comparing two email text bodies.
    """

    return calculate_cosine_similarity(
        first_body,
        second_body,
    )