import base64
import asyncio
import csv
import io
import json
import re
import socket
from datetime import datetime, timedelta, timezone
from ipaddress import ip_address
from urllib.parse import urlsplit
from uuid import UUID, uuid4

import httpx
from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import func, select

from app.core.config import settings
from app.core.database import SessionLocal
from app.modules.audit_security_admin.audit.service import record_audit
from app.modules.detection.models import DetectionRecord
from app.modules.emails.models import Email
from .integrations.detection_adapter import DetectionAdapter
from .integrations.email_adapter import EmailAdapter
from .models import ThreatFeed, ThreatFeedSync, ThreatIndicator, ThreatMatch, utc_now
from .repository import ThreatRepository
from .validators import normalize_indicator, validate_public_feed_url


class ThreatError(Exception):
    pass


class ThreatNotFound(ThreatError):
    pass


class ThreatConflict(ThreatError):
    pass


class ThreatValidationError(ThreatError):
    pass


def _credential_cipher():
    from hashlib import sha256

    key = base64.urlsafe_b64encode(sha256(settings.jwt_secret_key.encode()).digest())
    return Fernet(key)


def _as_utc(value):
    if value is None:
        return utc_now()
    return (
        value.replace(tzinfo=timezone.utc)
        if value.tzinfo is None
        else value.astimezone(timezone.utc)
    )


def _safe_feed_host(url):
    host = urlsplit(url).hostname
    try:
        addresses = {
            entry[4][0]
            for entry in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
        }
    except OSError as exc:
        raise ThreatValidationError("The feed host could not be resolved.") from exc
    if not addresses or any(not ip_address(address).is_global for address in addresses):
        raise ThreatValidationError(
            "Feed hosts must resolve only to public IP addresses."
        )


def _sync_error_message(error):
    """Return useful sync errors without exposing remote bodies or secrets."""
    if isinstance(error, httpx.HTTPStatusError):
        return f"Feed server returned HTTP {error.response.status_code}."
    if isinstance(error, httpx.TimeoutException):
        return "Feed request timed out."
    if isinstance(error, httpx.RequestError):
        return "Could not connect to the threat feed. Check its URL and availability."
    if isinstance(error, (ThreatValidationError, ValueError, RuntimeError)):
        return str(error)[:1000]
    return "Feed synchronization failed due to an internal error."


class ThreatService:
    def __init__(self, db):
        self.db = db
        self.repo = ThreatRepository(db)
        self.emails = EmailAdapter(db)
        self.detections = DetectionAdapter(db)

    @staticmethod
    def page_data(rows, total, page, page_size):
        return {
            "items": rows,
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": max(1, (total + page_size - 1) // page_size),
        }

    def indicators(self, **filters):
        rows, total = self.repo.list_indicators(**filters)
        return self.page_data(
            [self.repo.indicator_read(row) for row in rows],
            total,
            filters["page"],
            filters["page_size"],
        )

    def get_indicator(self, indicator_id):
        row = self.repo.indicator(indicator_id)
        if not row:
            raise ThreatNotFound("Indicator was not found.")
        return self.repo.indicator_read(row)

    def create_indicator(self, payload, actor):
        normalized = normalize_indicator(payload.value, payload.indicator_type)
        exists = self.db.scalar(
            select(ThreatIndicator.id).where(
                ThreatIndicator.normalized_value == normalized,
                ThreatIndicator.indicator_type == payload.indicator_type,
            )
        )
        if exists:
            raise ThreatConflict("This indicator already exists.")
        row = ThreatIndicator(
            id=uuid4(),
            value=payload.value.strip(),
            normalized_value=normalized,
            indicator_type=payload.indicator_type,
            severity=payload.severity,
            confidence=payload.confidence,
            source=payload.source,
            description=payload.description,
            expires_at=payload.expires_at,
            created_by_id=actor.id,
        )
        self.db.add(row)
        self.db.flush()
        matched = self._reconcile_indicator(row)
        record_audit(
            self.db,
            actor=actor,
            action="threat_indicator.created",
            target_type="threat_indicator",
            target_id=row.id,
            target_label=row.value,
            source="Threat Intelligence",
            details={"type": row.indicator_type, "matches_created": matched},
        )
        self.db.flush()
        return self.repo.indicator_read(row)

    def update_indicator(self, indicator_id, changes, actor):
        row = self.repo.indicator(indicator_id)
        if not row:
            raise ThreatNotFound("Indicator was not found.")
        if "value" in changes or "indicator_type" in changes:
            kind = changes.get("indicator_type") or row.indicator_type
            value = changes.get("value") or row.value
            normalized = normalize_indicator(value, kind)
            duplicate = self.db.scalar(
                select(ThreatIndicator.id).where(
                    ThreatIndicator.normalized_value == normalized,
                    ThreatIndicator.indicator_type == kind,
                    ThreatIndicator.id != row.id,
                )
            )
            if duplicate:
                raise ThreatConflict("Another indicator already uses this value.")
            row.value, row.normalized_value, row.indicator_type = (
                value.strip(),
                normalized,
                kind,
            )
        for key in ("severity", "confidence", "description", "expires_at"):
            if key in changes:
                setattr(row, key, changes[key])
        row.updated_at = utc_now()
        record_audit(
            self.db,
            actor=actor,
            action="threat_indicator.updated",
            target_type="threat_indicator",
            target_id=row.id,
            target_label=row.value,
            source="Threat Intelligence",
            details={"changed_fields": sorted(changes)},
        )
        self.db.flush()
        if row.status == "active":
            self._reconcile_indicator(row)
        return self.repo.indicator_read(row)

    def set_indicator_status(self, indicator_id, status, actor):
        row = self.repo.indicator(indicator_id)
        if not row:
            raise ThreatNotFound("Indicator was not found.")
        row.status = status
        row.updated_at = utc_now()
        record_audit(
            self.db,
            actor=actor,
            action=f"threat_indicator.{status}",
            target_type="threat_indicator",
            target_id=row.id,
            target_label=row.value,
            source="Threat Intelligence",
            details={},
        )
        return self.repo.indicator_read(row)

    def reconcile_email(self, email):
        """Match a newly collected email against active, non-expired IOCs."""
        now = utc_now()
        indicators = self.db.scalars(
            select(ThreatIndicator).where(
                ThreatIndicator.status == "active",
                (
                    ThreatIndicator.expires_at.is_(None)
                    | (ThreatIndicator.expires_at > now)
                ),
            )
        ).all()
        inserted = 0
        for indicator in indicators:
            field = self.emails.matched_field(
                email, indicator.normalized_value, indicator.indicator_type
            )
            if not field:
                continue
            exists = self.db.scalar(
                select(ThreatMatch.id).where(
                    ThreatMatch.email_id == email.id,
                    ThreatMatch.indicator_id == indicator.id,
                )
            )
            if exists:
                continue
            detection = self.detections.latest_for_email(email.id)
            self.db.add(
                ThreatMatch(
                    email_id=email.id,
                    detection_id=detection.id if detection else None,
                    indicator_id=indicator.id,
                    feed_id=indicator.feed_id,
                    matched_field=field,
                )
            )
            indicator.last_seen_at = max(
                _as_utc(indicator.last_seen_at),
                _as_utc(email.received_at or email.collected_at),
            )
            inserted += 1
        if inserted:
            self.db.flush()
        return inserted

    def reconcile_existing_data(self):
        """Backfill matches for already stored emails and active indicators."""
        now = utc_now()
        indicators = self.db.scalars(
            select(ThreatIndicator).where(
                ThreatIndicator.status == "active",
                ThreatIndicator.expires_at.is_(None)
                | (ThreatIndicator.expires_at > now),
            )
        ).all()
        created = 0
        for indicator in indicators:
            created += self._reconcile_indicator(indicator)
        return {"indicators_checked": len(indicators), "matches_created": created}

    def indicator_matches(self, indicator_id, page, page_size):
        if not self.repo.indicator(indicator_id):
            raise ThreatNotFound("Indicator was not found.")
        rows, total = self.repo.indicator_matches(
            indicator_id, page=page, page_size=page_size
        )
        return self.page_data(
            [self.repo.match_detail(row) for row in rows], total, page, page_size
        )

    def _reconcile_indicator(self, indicator):
        if indicator.status != "active" or (
            indicator.expires_at and _as_utc(indicator.expires_at) <= utc_now()
        ):
            return 0
        created = 0
        for email in self.emails.candidates(
            indicator.normalized_value, indicator.indicator_type
        ):
            field = self.emails.matched_field(
                email, indicator.normalized_value, indicator.indicator_type
            )
            if not field:
                continue
            exists = self.db.scalar(
                select(ThreatMatch.id).where(
                    ThreatMatch.email_id == email.id,
                    ThreatMatch.indicator_id == indicator.id,
                )
            )
            if exists:
                continue
            detection = self.detections.latest_for_email(email.id)
            self.db.add(
                ThreatMatch(
                    email_id=email.id,
                    detection_id=detection.id if detection else None,
                    indicator_id=indicator.id,
                    feed_id=indicator.feed_id,
                    matched_field=field,
                )
            )
            indicator.last_seen_at = max(
                _as_utc(indicator.last_seen_at),
                _as_utc(email.received_at or email.collected_at),
            )
            created += 1
        if created:
            self.db.flush()
        return created

    def feeds(self, **filters):
        rows, total = self.repo.list_feeds(**filters)
        return self.page_data(
            [self.repo.feed_read(row) for row in rows],
            total,
            filters["page"],
            filters["page_size"],
        )

    def feed_summary(self):
        return self.repo.feed_summary()

    def get_feed(self, feed_id):
        row = self.repo.feed(feed_id)
        if not row:
            raise ThreatNotFound("Threat feed was not found.")
        result = self.repo.feed_read(row)
        syncs, total = self.repo.list_syncs(feed_id, page=1, page_size=10)
        result["sync_history"] = self.page_data(
            [self.sync_read(item) for item in syncs], total, 1, 10
        )
        return result

    def create_feed(self, payload, actor):
        if payload.url:
            try:
                validate_public_feed_url(payload.url)
            except ValueError as exc:
                raise ThreatValidationError(str(exc)) from exc
        if self.db.scalar(
            select(ThreatFeed.id).where(
                func.lower(ThreatFeed.name) == payload.name.strip().lower()
            )
        ):
            raise ThreatConflict("A feed with this name already exists.")
        ciphertext = (
            _credential_cipher().encrypt(payload.credential.encode()).decode()
            if payload.credential
            else None
        )
        now = utc_now()
        row = ThreatFeed(
            id=uuid4(),
            name=payload.name.strip(),
            feed_type=payload.feed_type,
            url=payload.url,
            auth_type=payload.auth_type,
            credential_ciphertext=ciphertext,
            sync_interval_minutes=payload.sync_interval_minutes,
            description=payload.description,
            enabled=payload.enabled,
            next_sync_at=(
                now + timedelta(minutes=payload.sync_interval_minutes)
                if payload.enabled and payload.feed_type != "internal"
                else None
            ),
            created_by_id=actor.id,
        )
        self.db.add(row)
        self.db.flush()
        record_audit(
            self.db,
            actor=actor,
            action="threat_feed.created",
            target_type="threat_feed",
            target_id=row.id,
            target_label=row.name,
            source="Threat Intelligence",
            details={"feed_type": row.feed_type, "auth_type": row.auth_type},
        )
        return self.repo.feed_read(row)

    def update_feed(self, feed_id, changes, actor):
        row = self.repo.feed(feed_id)
        if not row:
            raise ThreatNotFound("Threat feed was not found.")
        effective_type = changes.get("feed_type", row.feed_type)
        effective_url = changes.get("url", row.url)
        effective_auth = changes.get("auth_type", row.auth_type)
        if effective_type == "internal" and effective_auth != "none":
            raise ThreatValidationError(
                "Internal feeds do not use external authentication."
            )
        if effective_type == "internal" and effective_url:
            raise ThreatValidationError("Internal feeds do not use an external URL.")
        if effective_type != "internal" and not effective_url:
            raise ThreatValidationError("An external feed URL is required.")
        if effective_url:
            try:
                validate_public_feed_url(effective_url)
            except ValueError as exc:
                raise ThreatValidationError(str(exc)) from exc
        if (
            effective_auth != "none"
            and not row.credential_ciphertext
            and not changes.get("credential")
        ):
            raise ThreatValidationError(
                "A credential is required for the selected authentication type."
            )
        if changes.get("credential"):
            if effective_auth == "none":
                raise ThreatValidationError(
                    "Choose an authentication type before setting a new credential."
                )
            row.credential_ciphertext = (
                _credential_cipher()
                .encrypt(changes.pop("credential").encode())
                .decode()
            )
        elif effective_auth == "none":
            row.credential_ciphertext = None
        for key, value in changes.items():
            if value is not None:
                setattr(row, key, value.strip() if key == "name" else value)
        if (
            ("sync_interval_minutes" in changes or "feed_type" in changes)
            and row.enabled
            and row.feed_type != "internal"
        ):
            now = utc_now()
            row.next_sync_at = max(_as_utc(row.last_sync_at), now) + timedelta(
                minutes=row.sync_interval_minutes
            )
        if "enabled" in changes:
            row.next_sync_at = (
                utc_now() + timedelta(minutes=row.sync_interval_minutes)
                if row.enabled and row.feed_type != "internal"
                else None
            )
        row.updated_at = utc_now()
        record_audit(
            self.db,
            actor=actor,
            action="threat_feed.updated",
            target_type="threat_feed",
            target_id=row.id,
            target_label=row.name,
            source="Threat Intelligence",
            details={"changed_fields": sorted(changes)},
        )
        return self.repo.feed_read(row)

    def sync_history(self, feed_id, page, page_size):
        if not self.repo.feed(feed_id):
            raise ThreatNotFound("Threat feed was not found.")
        rows, total = self.repo.list_syncs(feed_id, page=page, page_size=page_size)
        return self.page_data(
            [self.sync_read(row) for row in rows], total, page, page_size
        )

    @staticmethod
    def sync_read(row):
        return {
            "id": row.id,
            "feed_id": row.feed_id,
            "status": row.status,
            "imported_count": row.imported_count,
            "error_summary": row.error_summary,
            "started_at": row.started_at,
            "completed_at": row.completed_at,
        }

    def queue_sync(self, feed_id, actor):
        feed = self.repo.feed(feed_id)
        if not feed:
            raise ThreatNotFound("Threat feed was not found.")
        if not feed.enabled:
            raise ThreatConflict("Enable this feed before synchronizing it.")
        if feed.feed_type == "internal":
            raise ThreatValidationError(
                "Internal feeds are populated by manual indicator management."
            )
        if feed.sync_status in {"queued", "running"}:
            raise ThreatConflict("A synchronization is already active for this feed.")
        sync = ThreatFeedSync(feed_id=feed.id, status="queued")
        feed.sync_status = "queued"
        self.db.add(sync)
        self.db.flush()
        record_audit(
            self.db,
            actor=actor,
            action="threat_feed.sync_queued",
            target_type="threat_feed",
            target_id=feed.id,
            target_label=feed.name,
            source="Threat Intelligence",
            details={"sync_id": str(sync.id)},
        )
        return self.sync_read(sync)

    def list_matches(
        self,
        *,
        page,
        page_size,
        search=None,
        start=None,
        end=None,
        classification=None,
        severity=None,
        indicator_type=None,
        feed_id=None,
        status=None,
    ):
        rows, total = self.repo.list_matches(
            page=page,
            page_size=page_size,
            search=search,
            start=start,
            end=end,
            classification=classification,
            severity=severity,
            indicator_type=indicator_type,
            feed_id=feed_id,
            status=status,
        )
        return self.page_data(
            [self.repo.match_detail(row) for row in rows], total, page, page_size
        )

    def match_detail(self, match_id):
        match = self.repo.match(match_id)
        if not match:
            raise ThreatNotFound("Threat match was not found.")
        return self.repo.match_detail(match)

    def update_match_status(self, match_id, match_status, actor):
        match = self.repo.match(match_id)
        if not match:
            raise ThreatNotFound("Threat match was not found.")
        match.match_status = match_status
        record_audit(
            self.db,
            actor=actor,
            action=f"threat_match.{match_status}",
            target_type="threat_match",
            target_id=match.id,
            target_label=str(match.email_id),
            source="Threat Intelligence",
            details={"indicator_id": str(match.indicator_id)},
        )
        return self.repo.match_detail(match)

    def overview(self, *, start, end, threat_type=None, severity=None, feed_id=None):
        return self.repo.overview(start, end, threat_type, severity, feed_id)

    def match_summary(
        self,
        *,
        start,
        end,
        severity=None,
        indicator_type=None,
        feed_id=None,
        classification=None,
    ):
        return self.repo.match_summary(
            start,
            end,
            severity=severity,
            indicator_type=indicator_type,
            feed_id=feed_id,
            classification=classification,
        )


def _extract_records(feed_type, body):
    text = body.decode("utf-8-sig", errors="replace")
    if feed_type == "csv":
        records = list(csv.DictReader(io.StringIO(text)))
    else:
        data = json.loads(text)
        # TAXII 2.1 collections return an ``objects`` array alongside
        # ``more`` and ``next``. STIX Bundles use the same array shape.
        records = (
            data.get("objects", data.get("indicators", data.get("items", [])))
            if isinstance(data, dict)
            else data
        )
    if not isinstance(records, list):
        raise ValueError("Feed payload must contain an array of indicator records.")
    result = []
    pattern_re = re.compile(
        r"\[\s*(ipv4-addr|ipv6-addr|domain-name|url|email-addr|file)\s*:[^=]+?=\s*['\"]([^'\"]+)['\"]",
        re.I,
    )
    for record in records[:10000]:
        if not isinstance(record, dict):
            continue
        value = (
            record.get("value")
            or record.get("indicator")
            or record.get("indicator_value")
            or record.get("ioc")
            or record.get("ioc_value")
            or record.get("pattern")
        )
        kind = (
            record.get("indicator_type")
            or record.get("ioc_type")
            or record.get("threat_type")
            or record.get("type")
        )
        if str(record.get("type", "")).lower() == "indicator" and record.get("pattern"):
            parsed = pattern_re.search(record["pattern"])
            if parsed:
                kind = {
                    "ipv4-addr": "ip",
                    "ipv6-addr": "ip",
                    "domain-name": "domain",
                    "url": "url",
                    "email-addr": "email",
                    "file": "hash",
                }.get(parsed.group(1).lower())
                value = parsed.group(2)
                if kind == "hash":
                    kind = "hash"
        kind_map = {
            "ipv4": "ip",
            "ipv4-addr": "ip",
            "ipv6": "ip",
            "ipv6-addr": "ip",
            "ip_address": "ip",
            "ip-address": "ip",
            "domain-name": "domain",
            "fqdn": "domain",
            "sha-256": "hash",
            "sha256": "hash",
            "md5": "hash",
            "sha-1": "hash",
            "sha1": "hash",
            "email-addr": "email",
            "email_address": "email",
            "ioc": "hash",
        }
        kind = kind_map.get(str(kind).lower(), str(kind).lower()) if kind else kind
        if kind not in {"ip", "domain", "url", "hash", "email"} or not isinstance(
            value, str
        ):
            continue
        try:
            normalized = normalize_indicator(value, kind)
        except ValueError:
            continue
        result.append(
            {
                "value": value,
                "normalized_value": normalized,
                "indicator_type": kind,
                "severity": (
                    str(record.get("severity", "medium")).lower()
                    if str(record.get("severity", "medium")).lower()
                    in {"low", "medium", "high", "critical"}
                    else "medium"
                ),
                "confidence": (
                    max(0, min(100, int(record.get("confidence", 50))))
                    if str(record.get("confidence", "50")).isdigit()
                    else 50
                ),
                "description": str(record.get("description", ""))[:10000] or None,
            }
        )
    return result


def _fetch_feed_records(client, feed, headers, auth):
    """Fetch a bounded feed payload, following TAXII 2.1 pagination tokens.

    A feed URL must point at the STIX/TAXII collection objects endpoint.
    Only TAXII's opaque ``next`` token is followed; arbitrary remote-provided
    URLs are never requested. This keeps pagination on the configured host.
    """
    origin = urlsplit(feed.url)
    request_headers = dict(headers)
    if feed.feed_type == "stix_taxii":
        request_headers["Accept"] = (
            "application/taxii+json;version=2.1, application/stix+json"
        )

    records = []
    next_token = None
    seen_tokens = set()
    total_bytes = 0

    for _page in range(100):
        validate_public_feed_url(feed.url)
        _safe_feed_host(feed.url)
        page_chunks = []
        page_bytes = 0
        with client.stream(
            "GET",
            feed.url,
            params={"next": next_token} if next_token else None,
            headers=request_headers,
            auth=auth,
        ) as response:
            response.raise_for_status()
            response_origin = urlsplit(str(response.request.url))
            if (
                response_origin.scheme != origin.scheme
                or response_origin.hostname != origin.hostname
                or response_origin.port != origin.port
            ):
                raise RuntimeError(
                    "The feed returned a pagination request to a different host."
                )
            for chunk in response.iter_bytes():
                page_bytes += len(chunk)
                total_bytes += len(chunk)
                if page_bytes > 5_000_000 or total_bytes > 25_000_000:
                    raise RuntimeError("Threat feed exceeded its import size limit.")
                page_chunks.append(chunk)

        body = b"".join(page_chunks)
        records.extend(_extract_records(feed.feed_type, body))
        if len(records) > 100_000:
            raise RuntimeError(
                "Threat feed exceeded the 100,000 indicator import limit."
            )

        if feed.feed_type != "stix_taxii":
            return records

        try:
            page_data = json.loads(body.decode("utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RuntimeError("STIX/TAXII feed response was not valid JSON.") from exc
        if not isinstance(page_data, dict) or not page_data.get("more"):
            return records

        next_token = page_data.get("next")
        if not isinstance(next_token, str) or not next_token.strip():
            raise RuntimeError(
                "TAXII response indicated more data without a next token."
            )
        if next_token in seen_tokens:
            raise RuntimeError("TAXII feed repeated a pagination token.")
        seen_tokens.add(next_token)

    raise RuntimeError("TAXII feed exceeded the 100 page synchronization limit.")


def execute_feed_sync(sync_id: UUID):
    db = SessionLocal()
    try:
        sync = db.get(ThreatFeedSync, sync_id)
        if not sync:
            return
        feed = db.get(ThreatFeed, sync.feed_id)
        if not feed or not feed.enabled:
            raise RuntimeError("Feed is missing or disabled.")
        sync.status = "running"
        feed.sync_status = "running"
        sync.started_at = utc_now()
        db.commit()
        validate_public_feed_url(feed.url)
        _safe_feed_host(feed.url)
        headers = {"Accept": "application/json, text/csv, application/stix+json"}
        auth = None
        secret = None
        if feed.credential_ciphertext:
            try:
                secret = (
                    _credential_cipher()
                    .decrypt(feed.credential_ciphertext.encode())
                    .decode()
                )
            except InvalidToken as exc:
                raise RuntimeError(
                    "Saved feed credential could not be decrypted; update the credential."
                ) from exc
        if feed.auth_type == "api_key":
            headers["X-API-Key"] = secret
        elif feed.auth_type == "bearer":
            headers["Authorization"] = f"Bearer {secret}"
        elif feed.auth_type == "basic":
            username, sep, password = secret.partition(":")
            if not sep:
                raise RuntimeError(
                    "Basic credentials must be entered as username:password."
                )
            auth = (username, password)
        with httpx.Client(timeout=20, follow_redirects=False, verify=True) as client:
            records = _fetch_feed_records(client, feed, headers, auth)
        imported = 0
        service = ThreatService(db)
        for item in records:
            existing = db.scalar(
                select(ThreatIndicator).where(
                    ThreatIndicator.normalized_value == item["normalized_value"],
                    ThreatIndicator.indicator_type == item["indicator_type"],
                )
            )
            if existing:
                if existing.source == "manual":
                    continue
                existing.feed_id = feed.id
                existing.source = "feed"
                existing.severity = item["severity"]
                existing.confidence = item["confidence"]
                existing.description = item["description"] or existing.description
                existing.status = "active"
                existing.last_seen_at = utc_now()
                indicator = existing
            else:
                indicator = ThreatIndicator(
                    **item, feed_id=feed.id, source="feed", status="active"
                )
                db.add(indicator)
                db.flush()
                imported += 1
            service._reconcile_indicator(indicator)
        sync.status = "success"
        sync.imported_count = imported
        sync.completed_at = utc_now()
        feed.sync_status = "success"
        feed.imported_indicator_count = int(
            db.scalar(
                select(func.count(ThreatIndicator.id)).where(
                    ThreatIndicator.feed_id == feed.id
                )
            )
            or 0
        )
        feed.last_sync_at = sync.completed_at
        feed.next_sync_at = sync.completed_at + timedelta(
            minutes=feed.sync_interval_minutes
        )
        feed.latest_error = None
        record_audit(
            db,
            actor=None,
            action="threat_feed.sync_completed",
            target_type="threat_feed",
            target_id=feed.id,
            target_label=feed.name,
            source="Threat Intelligence",
            details={"sync_id": str(sync.id), "imported_count": imported},
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        sync = db.get(ThreatFeedSync, sync_id)
        if sync:
            sync.status = "failed"
            sync.error_summary = _sync_error_message(exc)
            sync.completed_at = utc_now()
            feed = db.get(ThreatFeed, sync.feed_id)
            if feed:
                feed.sync_status = "failed"
                feed.latest_error = sync.error_summary
                feed.last_sync_at = sync.completed_at
                record_audit(
                    db,
                    actor=None,
                    action="threat_feed.sync_failed",
                    target_type="threat_feed",
                    target_id=feed.id,
                    target_label=feed.name,
                    status="failure",
                    severity="high",
                    source="Threat Intelligence",
                    details={
                        "sync_id": str(sync.id),
                        "error_summary": sync.error_summary,
                    },
                )
            db.commit()
    finally:
        db.close()


async def run_feed_scheduler(stop_event: asyncio.Event, *, interval_seconds: int = 30):
    """Periodically queue due feeds; each API worker owns its own scheduler."""
    while not stop_event.is_set():
        db = SessionLocal()
        queued = []
        try:
            now = utc_now()
            due = db.scalars(
                select(ThreatFeed)
                .where(
                    ThreatFeed.enabled.is_(True),
                    ThreatFeed.feed_type != "internal",
                    ThreatFeed.next_sync_at.is_not(None),
                    ThreatFeed.next_sync_at <= now,
                    ThreatFeed.sync_status.not_in(("queued", "running")),
                )
                .limit(20)
            ).all()
            for feed in due:
                # Conditional update is the claim step, so concurrent API workers
                # cannot queue the same feed at the same time.
                claimed = (
                    db.query(ThreatFeed)
                    .filter(
                        ThreatFeed.id == feed.id,
                        ThreatFeed.enabled.is_(True),
                        ThreatFeed.sync_status.not_in(("queued", "running")),
                    )
                    .update(
                        {ThreatFeed.sync_status: "queued"}, synchronize_session=False
                    )
                )
                if not claimed:
                    continue
                sync = ThreatFeedSync(feed_id=feed.id, status="queued", started_at=now)
                db.add(sync)
                db.flush()
                record_audit(
                    db,
                    actor=None,
                    action="threat_feed.sync_scheduled",
                    target_type="threat_feed",
                    target_id=feed.id,
                    target_label=feed.name,
                    source="Threat Intelligence",
                    details={"sync_id": str(sync.id)},
                )
                queued.append(sync.id)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()
        if queued:
            await asyncio.gather(
                *(asyncio.to_thread(execute_feed_sync, sync_id) for sync_id in queued),
                return_exceptions=True,
            )
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval_seconds)
        except asyncio.TimeoutError:
            pass
