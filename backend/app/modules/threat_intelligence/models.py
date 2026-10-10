from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Uuid,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class ThreatIndicator(Base):
    __tablename__ = "threat_indicators"
    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    value: Mapped[str] = mapped_column(String(2048), nullable=False)
    normalized_value: Mapped[str] = mapped_column(
        String(2048), nullable=False, index=True
    )
    indicator_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(
        String(20), nullable=False, default="medium", index=True
    )
    confidence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source: Mapped[str] = mapped_column(
        String(20), nullable=False, default="manual", index=True
    )
    feed_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("threat_feeds.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", index=True
    )
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    created_by_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )
    __table_args__ = (
        CheckConstraint(
            "indicator_type IN ('ip','domain','url','hash','email')",
            name="ck_threat_indicator_type",
        ),
        CheckConstraint(
            "severity IN ('low','medium','high','critical')",
            name="ck_threat_indicator_severity",
        ),
        CheckConstraint(
            "status IN ('active','inactive','expired')",
            name="ck_threat_indicator_status",
        ),
        CheckConstraint(
            "confidence IS NULL OR confidence BETWEEN 0 AND 100",
            name="ck_threat_indicator_confidence",
        ),
        UniqueConstraint(
            "normalized_value", "indicator_type", name="uq_threat_indicator_value_type"
        ),
    )


class ThreatFeed(Base):
    __tablename__ = "threat_feeds"
    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    name: Mapped[str] = mapped_column(
        String(180), nullable=False, unique=True, index=True
    )
    feed_type: Mapped[str] = mapped_column(String(20), nullable=False)
    url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    auth_type: Mapped[str] = mapped_column(String(20), nullable=False, default="none")
    credential_ciphertext: Mapped[str | None] = mapped_column(Text, nullable=True)
    sync_interval_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=60
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, index=True
    )
    sync_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="never_synced", index=True
    )
    imported_indicator_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    last_sync_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    next_sync_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    latest_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )
    __table_args__ = (
        CheckConstraint(
            "feed_type IN ('stix_taxii','csv','json','api','internal')",
            name="ck_threat_feed_type",
        ),
        CheckConstraint(
            "auth_type IN ('none','api_key','bearer','basic')",
            name="ck_threat_feed_auth",
        ),
        CheckConstraint(
            "sync_status IN ('never_synced','queued','running','success','failed')",
            name="ck_threat_feed_sync_status",
        ),
        CheckConstraint(
            "sync_interval_minutes BETWEEN 5 AND 10080",
            name="ck_threat_feed_sync_interval",
        ),
    )


class ThreatFeedSync(Base):
    __tablename__ = "threat_feed_syncs"
    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    feed_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("threat_feeds.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="queued", index=True
    )
    imported_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    __table_args__ = (
        CheckConstraint(
            "status IN ('queued','running','success','failed')",
            name="ck_threat_feed_sync_status",
        ),
    )


class ThreatMatch(Base):
    __tablename__ = "threat_matches"
    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    email_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("emails.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    detection_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("email_detections.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    indicator_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("threat_indicators.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    feed_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("threat_feeds.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    match_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="new", index=True
    )
    matched_field: Mapped[str] = mapped_column(
        String(40), nullable=False, default="content"
    )
    matched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    __table_args__ = (
        CheckConstraint(
            "match_status IN ('new','reviewed','investigating','resolved')",
            name="ck_threat_match_status",
        ),
        Index(
            "uq_threat_match_email_indicator", "email_id", "indicator_id", unique=True
        ),
    )
