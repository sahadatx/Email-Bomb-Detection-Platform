import ipaddress
import re
from urllib.parse import urlsplit


def normalize_indicator(value: str, kind: str) -> str:
    value = value.strip()
    if kind == "ip":
        try:
            return str(ipaddress.ip_address(value))
        except ValueError as exc:
            raise ValueError("Enter a valid IPv4 or IPv6 address.") from exc
    if kind == "domain":
        domain = value.rstrip(".").lower()
        if len(domain) > 253 or not re.fullmatch(
            r"(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)*[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?",
            domain,
        ):
            raise ValueError("Enter a valid domain name without a URL scheme.")
        return domain
    if kind == "url":
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("Enter an HTTP or HTTPS indicator URL.")
        return value.rstrip("/").lower()
    if kind == "email":
        candidate = value.lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", candidate):
            raise ValueError("Enter a valid email address indicator.")
        return candidate
    if kind == "hash":
        candidate = value.lower()
        if not re.fullmatch(
            r"(?:[a-f0-9]{32}|[a-f0-9]{40}|[a-f0-9]{64}|[a-f0-9]{128})", candidate
        ):
            raise ValueError(
                "Hash indicators must be valid MD5, SHA-1, SHA-256, or SHA-512 hex values."
            )
        return candidate
    raise ValueError("Unsupported indicator type.")


def validate_public_feed_url(url: str) -> str:
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
    ):
        raise ValueError(
            "External threat feeds must use HTTPS and must not embed credentials in the URL."
        )
    if parsed.port not in (None, 443):
        raise ValueError("Threat feed URLs may use only the default HTTPS port.")
    host = parsed.hostname.lower().rstrip(".")
    if (
        host in {"localhost", "localhost.localdomain"}
        or host.endswith(".localhost")
        or host.endswith(".local")
    ):
        raise ValueError("Local network feed URLs are not allowed.")
    try:
        ip = ipaddress.ip_address(host)
        if not ip.is_global:
            raise ValueError("Feed URL must resolve to a public address.")
    except ValueError as exc:
        if str(exc) == "Feed URL must resolve to a public address.":
            raise
        if ":" in host:
            raise ValueError("Invalid feed hostname.") from exc
    return url
