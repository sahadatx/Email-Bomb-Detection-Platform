from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import String, func, or_, select

from app.modules.detection.models import DetectionRecord
from app.modules.emails.models import Email
from .models import ThreatFeed, ThreatFeedSync, ThreatIndicator, ThreatMatch


class ThreatRepository:
    def __init__(self, db):
        self.db = db

    def indicator(self, row_id):
        return self.db.get(ThreatIndicator, row_id)

    def feed(self, row_id):
        return self.db.get(ThreatFeed, row_id)

    def match(self, row_id):
        return self.db.get(ThreatMatch, row_id)

    def list_indicators(
        self,
        *,
        page,
        page_size,
        search=None,
        indicator_type=None,
        severity=None,
        status=None,
        source=None,
        feed_id=None,
    ):
        stmt = select(ThreatIndicator)
        if search:
            stmt = stmt.where(ThreatIndicator.value.ilike(f"%{search.strip()}%"))
        if indicator_type:
            stmt = stmt.where(ThreatIndicator.indicator_type == indicator_type)
        if severity:
            stmt = stmt.where(ThreatIndicator.severity == severity)
        now = datetime.now(timezone.utc)
        if status == "expired":
            stmt = stmt.where(
                ThreatIndicator.expires_at.is_not(None),
                ThreatIndicator.expires_at <= now,
            )
        elif status == "active":
            stmt = stmt.where(
                ThreatIndicator.status == "active",
                (
                    ThreatIndicator.expires_at.is_(None)
                    | (ThreatIndicator.expires_at > now)
                ),
            )
        elif status:
            stmt = stmt.where(ThreatIndicator.status == status)
        if source:
            stmt = stmt.where(ThreatIndicator.source == source)
        if feed_id:
            stmt = stmt.where(ThreatIndicator.feed_id == feed_id)
        total = int(
            self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        )
        rows = self.db.scalars(
            stmt.order_by(ThreatIndicator.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
        return rows, total

    def indicator_matches(self, indicator_id, *, page=1, page_size=30):
        stmt = select(ThreatMatch).where(ThreatMatch.indicator_id == indicator_id)
        total = int(
            self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        )
        return (
            self.db.scalars(
                stmt.order_by(ThreatMatch.matched_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            ).all(),
            total,
        )

    def list_feeds(
        self,
        *,
        page,
        page_size,
        search=None,
        status=None,
        feed_type=None,
        sync_status=None,
    ):
        stmt = select(ThreatFeed)
        if search:
            stmt = stmt.where(ThreatFeed.name.ilike(f"%{search.strip()}%"))
        if status == "active":
            stmt = stmt.where(ThreatFeed.enabled.is_(True))
        elif status == "inactive":
            stmt = stmt.where(ThreatFeed.enabled.is_(False))
        if feed_type:
            stmt = stmt.where(ThreatFeed.feed_type == feed_type)
        if sync_status:
            stmt = stmt.where(ThreatFeed.sync_status == sync_status)
        total = int(
            self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        )
        rows = self.db.scalars(
            stmt.order_by(ThreatFeed.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
        return rows, total

    def feed_summary(self):
        total = int(self.db.scalar(select(func.count(ThreatFeed.id))) or 0)
        active = int(
            self.db.scalar(
                select(func.count(ThreatFeed.id)).where(ThreatFeed.enabled.is_(True))
            )
            or 0
        )
        failed = int(
            self.db.scalar(
                select(func.count(ThreatFeed.id)).where(
                    ThreatFeed.sync_status == "failed"
                )
            )
            or 0
        )
        imported = int(
            self.db.scalar(
                select(func.coalesce(func.sum(ThreatFeed.imported_indicator_count), 0))
            )
            or 0
        )
        return {
            "total_feeds": total,
            "active_feeds": active,
            "sync_failed": failed,
            "imported_indicators": imported,
        }

    def list_syncs(self, feed_id, *, page, page_size):
        stmt = select(ThreatFeedSync).where(ThreatFeedSync.feed_id == feed_id)
        total = int(
            self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        )
        rows = self.db.scalars(
            stmt.order_by(ThreatFeedSync.started_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
        return rows, total

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
        stmt = (
            select(ThreatMatch)
            .join(ThreatIndicator, ThreatMatch.indicator_id == ThreatIndicator.id)
            .join(Email, ThreatMatch.email_id == Email.id)
        )
        if search:
            pattern = f"%{search.strip()}%"
            try:
                exact_email_id = UUID(search.strip())
                email_search = Email.id == exact_email_id
            except ValueError:
                email_search = Email.id.cast(String).ilike(pattern)
            stmt = stmt.where(
                or_(
                    email_search,
                    ThreatIndicator.value.ilike(pattern),
                    ThreatMatch.detection_id.cast(String).ilike(pattern),
                )
            )
        if start:
            stmt = stmt.where(ThreatMatch.matched_at >= start)
        if end:
            stmt = stmt.where(ThreatMatch.matched_at <= end)
        if classification:
            latest_detection_id = (
                select(DetectionRecord.id)
                .where(
                    DetectionRecord.email_id == ThreatMatch.email_id,
                    DetectionRecord.status == "completed",
                    DetectionRecord.predicted_label.in_(("normal", "bomb")),
                )
                .order_by(DetectionRecord.created_at.desc(), DetectionRecord.id.desc())
                .limit(1)
                .correlate(ThreatMatch)
                .scalar_subquery()
            )
            if classification == "unknown":
                stmt = stmt.where(latest_detection_id.is_(None))
            else:
                stmt = stmt.where(
                    latest_detection_id.in_(
                        select(DetectionRecord.id).where(
                            DetectionRecord.predicted_label == classification
                        )
                    )
                )
        if severity:
            stmt = stmt.where(ThreatIndicator.severity == severity)
        if indicator_type:
            stmt = stmt.where(ThreatIndicator.indicator_type == indicator_type)
        if feed_id:
            stmt = stmt.where(ThreatMatch.feed_id == feed_id)
        if status:
            stmt = stmt.where(ThreatMatch.match_status == status)
        total = int(
            self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        )
        rows = self.db.scalars(
            stmt.order_by(ThreatMatch.matched_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
        return rows, total

    def match_detail(self, match):
        indicator = self.indicator(match.indicator_id)
        email = self.db.get(Email, match.email_id)
        feed = self.feed(match.feed_id) if match.feed_id else None
        # A match can outlive its original detection, so show the latest
        # completed result for the email and fall back to the stored link.
        latest = self.db.scalar(
            select(DetectionRecord)
            .where(
                DetectionRecord.email_id == match.email_id,
                DetectionRecord.status == "completed",
                DetectionRecord.predicted_label.in_(("normal", "bomb")),
            )
            .order_by(DetectionRecord.created_at.desc(), DetectionRecord.id.desc())
            .limit(1)
        )
        if not latest and match.detection_id:
            linked = self.db.get(DetectionRecord, match.detection_id)
            if (
                linked
                and linked.status == "completed"
                and linked.predicted_label in ("normal", "bomb")
            ):
                latest = linked
        return {
            "id": match.id,
            "email_id": match.email_id,
            "email_label": email.sender or email.subject if email else None,
            # Classification in threat match views reflects the email's current
            # detection result. A match can outlive the detection that created it.
            "detection_id": latest.id if latest else None,
            "indicator_id": indicator.id,
            "indicator_value": indicator.value,
            "indicator_type": indicator.indicator_type,
            "severity": indicator.severity,
            "classification": latest.predicted_label if latest else None,
            "feed_id": match.feed_id,
            "feed_name": feed.name if feed else None,
            "match_status": match.match_status,
            "matched_field": match.matched_field,
            "matched_at": match.matched_at,
        }

    def indicator_read(self, row):
        feed = self.feed(row.feed_id) if row.feed_id else None
        match_count = int(
            self.db.scalar(
                select(func.count(ThreatMatch.id)).where(
                    ThreatMatch.indicator_id == row.id
                )
            )
            or 0
        )
        expires_at = row.expires_at
        if expires_at and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        effective_status = (
            "expired"
            if expires_at
            and expires_at <= datetime.now(timezone.utc)
            and row.status == "active"
            else row.status
        )
        return {
            "id": row.id,
            "value": row.value,
            "indicator_type": row.indicator_type,
            "severity": row.severity,
            "confidence": row.confidence,
            "source": row.source,
            "feed_id": row.feed_id,
            "feed_name": feed.name if feed else None,
            "description": row.description,
            "status": effective_status,
            "first_seen_at": row.first_seen_at,
            "last_seen_at": row.last_seen_at,
            "expires_at": row.expires_at,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
            "matches_count": match_count,
        }

    @staticmethod
    def feed_read(row):
        return {
            "id": row.id,
            "name": row.name,
            "feed_type": row.feed_type,
            "url": row.url,
            "auth_type": row.auth_type,
            "has_credential": bool(row.credential_ciphertext),
            "sync_interval_minutes": row.sync_interval_minutes,
            "description": row.description,
            "enabled": row.enabled,
            "sync_status": row.sync_status,
            "imported_indicator_count": row.imported_indicator_count,
            "last_sync_at": row.last_sync_at,
            "next_sync_at": row.next_sync_at,
            "latest_error": row.latest_error,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }

    def overview(
        self,
        start: datetime,
        end: datetime,
        threat_type=None,
        severity=None,
        feed_id=None,
    ):
        base = (
            select(ThreatMatch)
            .join(ThreatIndicator, ThreatMatch.indicator_id == ThreatIndicator.id)
            .where(ThreatMatch.matched_at >= start, ThreatMatch.matched_at <= end)
        )
        if threat_type:
            base = base.where(ThreatIndicator.indicator_type == threat_type)
        if severity:
            base = base.where(ThreatIndicator.severity == severity)
        if feed_id:
            base = base.where(ThreatMatch.feed_id == feed_id)
        now = datetime.now(timezone.utc)
        indicator_filters = [
            ThreatIndicator.status == "active",
            (ThreatIndicator.expires_at.is_(None) | (ThreatIndicator.expires_at > now)),
            ThreatIndicator.created_at >= start,
            ThreatIndicator.created_at <= end,
        ]
        if threat_type:
            indicator_filters.append(ThreatIndicator.indicator_type == threat_type)
        if severity:
            indicator_filters.append(ThreatIndicator.severity == severity)
        if feed_id:
            indicator_filters.append(ThreatIndicator.feed_id == feed_id)
        total_indicators = int(
            self.db.scalar(
                select(func.count(ThreatIndicator.id)).where(*indicator_filters)
            )
            or 0
        )
        feed_filters = [ThreatFeed.enabled.is_(True)]
        if feed_id:
            feed_filters.append(ThreatFeed.id == feed_id)
        active_feeds = int(
            self.db.scalar(select(func.count(ThreatFeed.id)).where(*feed_filters)) or 0
        )
        total_matches = int(
            self.db.scalar(select(func.count()).select_from(base.subquery())) or 0
        )
        critical_base = base.where(ThreatIndicator.severity == "critical")
        critical = int(
            self.db.scalar(select(func.count()).select_from(critical_base.subquery()))
            or 0
        )
        type_rows = self.db.execute(
            base.with_only_columns(
                ThreatIndicator.indicator_type, func.count(ThreatMatch.id)
            ).group_by(ThreatIndicator.indicator_type)
        ).all()
        severity_rows = self.db.execute(
            base.with_only_columns(
                ThreatIndicator.severity, func.count(ThreatMatch.id)
            ).group_by(ThreatIndicator.severity)
        ).all()
        trend_rows = self.db.execute(
            base.with_only_columns(
                func.date(ThreatMatch.matched_at), func.count(ThreatMatch.id)
            )
            .group_by(func.date(ThreatMatch.matched_at))
            .order_by(func.date(ThreatMatch.matched_at))
        ).all()
        indicator_activity_query = select(
            func.date(ThreatIndicator.created_at),
            func.count(ThreatIndicator.id),
        ).where(
            ThreatIndicator.created_at >= start,
            ThreatIndicator.created_at <= end,
        )
        if threat_type:
            indicator_activity_query = indicator_activity_query.where(
                ThreatIndicator.indicator_type == threat_type
            )
        if severity:
            indicator_activity_query = indicator_activity_query.where(
                ThreatIndicator.severity == severity
            )
        if feed_id:
            indicator_activity_query = indicator_activity_query.where(
                ThreatIndicator.feed_id == feed_id
            )
        indicator_activity_rows = self.db.execute(
            indicator_activity_query.group_by(
                func.date(ThreatIndicator.created_at)
            ).order_by(func.date(ThreatIndicator.created_at))
        ).all()
        activity_by_date = {
            str(date): {"matches": int(count), "indicators": 0}
            for date, count in trend_rows
        }
        for date, count in indicator_activity_rows:
            activity_by_date.setdefault(str(date), {"matches": 0, "indicators": 0})[
                "indicators"
            ] = int(count)
        latest = self.db.scalars(
            base.order_by(ThreatMatch.matched_at.desc()).limit(5)
        ).all()
        return {
            "total_indicators": total_indicators,
            "active_feeds": active_feeds,
            "threat_matches": total_matches,
            "critical_threats": critical,
            "trends": [
                {"date": date, **values}
                for date, values in sorted(activity_by_date.items())
            ],
            "types": [{"type": key, "count": int(value)} for key, value in type_rows],
            "severities": [
                {"severity": key, "count": int(value)} for key, value in severity_rows
            ],
            "recent_matches": [self.match_detail(row) for row in latest],
            "data_sources": [
                "Threat indicators",
                "Threat feeds",
                "Stored email matches",
            ],
        }

    def match_summary(self, start=None, end=None, **filters):
        stmt = select(ThreatMatch).join(
            ThreatIndicator, ThreatMatch.indicator_id == ThreatIndicator.id
        )
        if start:
            stmt = stmt.where(ThreatMatch.matched_at >= start)
        if end:
            stmt = stmt.where(ThreatMatch.matched_at <= end)
        if filters.get("severity"):
            stmt = stmt.where(ThreatIndicator.severity == filters["severity"])
        if filters.get("indicator_type"):
            stmt = stmt.where(
                ThreatIndicator.indicator_type == filters["indicator_type"]
            )
        if filters.get("feed_id"):
            stmt = stmt.where(ThreatMatch.feed_id == filters["feed_id"])
        classification = filters.get("classification")
        if classification:
            latest_detection_id = (
                select(DetectionRecord.id)
                .where(
                    DetectionRecord.email_id == ThreatMatch.email_id,
                    DetectionRecord.status == "completed",
                    DetectionRecord.predicted_label.in_(("normal", "bomb")),
                )
                .order_by(DetectionRecord.created_at.desc(), DetectionRecord.id.desc())
                .limit(1)
                .correlate(ThreatMatch)
                .scalar_subquery()
            )
            if classification == "unknown":
                stmt = stmt.where(latest_detection_id.is_(None))
            else:
                stmt = stmt.where(
                    latest_detection_id.in_(
                        select(DetectionRecord.id).where(
                            DetectionRecord.predicted_label == classification
                        )
                    )
                )
        sub = stmt.subquery()
        return {
            "total_matches": int(
                self.db.scalar(select(func.count()).select_from(sub)) or 0
            ),
            "critical_matches": int(
                self.db.scalar(
                    select(func.count())
                    .select_from(sub)
                    .where(
                        sub.c.indicator_id.in_(
                            select(ThreatIndicator.id).where(
                                ThreatIndicator.severity == "critical"
                            )
                        )
                    )
                )
                or 0
            ),
            "matched_emails": int(
                self.db.scalar(select(func.count(func.distinct(sub.c.email_id)))) or 0
            ),
            "unique_indicators": int(
                self.db.scalar(select(func.count(func.distinct(sub.c.indicator_id))))
                or 0
            ),
        }
