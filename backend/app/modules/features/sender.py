from __future__ import annotations

import json
from email.utils import parseaddr
from pathlib import Path
from typing import Iterable


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_TRUSTED_DOMAINS_PATH = (
    Path(__file__).resolve().parents[4]
    / "config"
    / "trusted_domains.json"
)


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_email_address(value: str | None) -> str | None:
    """
    Normalize a sender email address.

    Rules:
    - Return None for missing/empty values.
    - Support both plain addresses and display-name formats.
    - Strip surrounding whitespace.
    - Lowercase the complete email address.
    - Reject values that do not contain a valid local/domain structure.
    """

    if not value:
        return None

    value = value.strip()

    if not value:
        return None

    _, address = parseaddr(value)

    address = address.strip().lower()

    if not address:
        return None

    if address.count("@") != 1:
        return None

    local_part, domain = address.rsplit("@", 1)

    if not local_part or not domain:
        return None

    if "." not in domain:
        return None

    if domain.startswith(".") or domain.endswith("."):
        return None

    return f"{local_part}@{domain}"


def extract_sender_email(
    sender: str | None,
) -> str | None:
    """
    Extract and normalize the sender email address.

    This is the implementation of F1.
    """

    return normalize_email_address(sender)


# ============================================================
# DOMAIN EXTRACTION
# ============================================================

def extract_sender_domain(
    sender_email: str | None,
) -> str | None:
    """
    Extract the normalized domain from a normalized sender address.
    """

    normalized = normalize_email_address(sender_email)

    if not normalized:
        return None

    _, domain = normalized.rsplit("@", 1)

    return domain


# ============================================================
# TRUSTED DOMAIN LOADING
# ============================================================

def normalize_domain(domain: str | None) -> str | None:
    """
    Normalize a domain for trusted-domain comparison.
    """

    if not domain:
        return None

    normalized = domain.strip().lower()

    if not normalized:
        return None

    # Remove an optional leading '@'.
    normalized = normalized.lstrip("@")

    # Remove trailing dot from fully-qualified domain names.
    normalized = normalized.rstrip(".")

    if not normalized:
        return None

    return normalized


def load_trusted_domains(
    path: str | Path | None = None,
) -> frozenset[str]:
    """
    Load trusted domains from config/trusted_domains.json.

    Supported JSON structures:

    1. List:
       [
           "gmail.com",
           "outlook.com"
       ]

    2. Object:
       {
           "domains": [
               "gmail.com",
               "outlook.com"
           ]
       }

    Invalid or missing files result in an empty trusted-domain
    set rather than silently treating an unknown domain as trusted.
    """

    config_path = (
        Path(path)
        if path is not None
        else DEFAULT_TRUSTED_DOMAINS_PATH
    )

    if not config_path.exists():
        return frozenset()

    try:
        with config_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError):
        return frozenset()

    if isinstance(data, dict):
        domains = data.get("domains", [])
    elif isinstance(data, list):
        domains = data
    else:
        return frozenset()

    if not isinstance(domains, Iterable) or isinstance(
        domains,
        (str, bytes),
    ):
        return frozenset()

    normalized_domains: set[str] = set()

    for domain in domains:
        if not isinstance(domain, str):
            continue

        normalized = normalize_domain(domain)

        if normalized:
            normalized_domains.add(normalized)

    return frozenset(normalized_domains)


# ============================================================
# DOMAIN MATCHING
# ============================================================

def is_trusted_domain(
    sender_domain: str | None,
    trusted_domains: Iterable[str],
) -> bool:
    """
    Determine whether a sender domain belongs to the trusted
    domain set.

    Matching rules:
    - Exact domain match is trusted.
    - A valid subdomain of a trusted domain is trusted.
    - Partial string matches are never trusted.

    Examples:

        sender: gmail.com
        trusted: gmail.com
        -> True

        sender: mail.gmail.com
        trusted: gmail.com
        -> True

        sender: fakegmail.com
        trusted: gmail.com
        -> False
    """

    normalized_sender_domain = normalize_domain(sender_domain)

    if not normalized_sender_domain:
        return False

    normalized_trusted_domains = {
        normalized
        for domain in trusted_domains
        if (normalized := normalize_domain(domain)) is not None
    }

    if normalized_sender_domain in normalized_trusted_domains:
        return True

    for trusted_domain in normalized_trusted_domains:
        if normalized_sender_domain.endswith(
            f".{trusted_domain}"
        ):
            return True

    return False


# ============================================================
# F2 — KNOWN DOMAIN INDICATOR
# ============================================================

def calculate_known_domain_indicator(
    sender_email: str | None,
    trusted_domains: Iterable[str],
) -> bool:
    """
    Calculate F2 — Known Domain Indicator.

    Returns True when the sender domain exactly matches or is a
    valid subdomain of a configured trusted domain.
    """

    sender_domain = extract_sender_domain(sender_email)

    return is_trusted_domain(
        sender_domain,
        trusted_domains,
    )


# ============================================================
# F1 + F2 EXTRACTION
# ============================================================

def extract_sender_features(
    sender: str | None,
    trusted_domains: Iterable[str] | None = None,
) -> dict[str, str | bool | None]:
    """
    Extract the sender-related features F1 and F2.

    Returns:

        {
            "f1_sender_email": "...",
            "f2_known_domain": True,
        }
    """

    sender_email = extract_sender_email(sender)

    domains = (
        trusted_domains
        if trusted_domains is not None
        else load_trusted_domains()
    )

    known_domain = calculate_known_domain_indicator(
        sender_email,
        domains,
    )

    return {
        "f1_sender_email": sender_email,
        "f2_known_domain": known_domain,
    }