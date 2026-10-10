"""Create threat intelligence indicators, feeds, and match records.

Revision ID: b1c2d3e4f5a6
Revises: a8b9c0d1e2f3
"""

from alembic import op
import sqlalchemy as sa

revision = "b1c2d3e4f5a6"
down_revision = "a8b9c0d1e2f3"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "threat_feeds",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(180), nullable=False),
        sa.Column("feed_type", sa.String(20), nullable=False),
        sa.Column("url", sa.String(2048), nullable=True),
        sa.Column("auth_type", sa.String(20), nullable=False),
        sa.Column("credential_ciphertext", sa.Text(), nullable=True),
        sa.Column("sync_interval_minutes", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("sync_status", sa.String(20), nullable=False),
        sa.Column("imported_indicator_count", sa.Integer(), nullable=False),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("latest_error", sa.Text(), nullable=True),
        sa.Column("created_by_id", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "feed_type IN ('stix_taxii','csv','json','api','internal')",
            name="ck_threat_feed_type",
        ),
        sa.CheckConstraint(
            "auth_type IN ('none','api_key','bearer','basic')",
            name="ck_threat_feed_auth",
        ),
        sa.CheckConstraint(
            "sync_status IN ('never_synced','queued','running','success','failed')",
            name="ck_threat_feed_sync_status",
        ),
        sa.CheckConstraint(
            "sync_interval_minutes BETWEEN 5 AND 10080",
            name="ck_threat_feed_sync_interval",
        ),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_threat_feeds_name", "threat_feeds", ["name"], unique=True)
    op.create_index("ix_threat_feeds_enabled", "threat_feeds", ["enabled"])
    op.create_index("ix_threat_feeds_sync_status", "threat_feeds", ["sync_status"])

    op.create_table(
        "threat_indicators",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("value", sa.String(2048), nullable=False),
        sa.Column("normalized_value", sa.String(2048), nullable=False),
        sa.Column("indicator_type", sa.String(20), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("confidence", sa.Integer(), nullable=True),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("feed_id", sa.Uuid(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_id", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "indicator_type IN ('ip','domain','url','hash','email')",
            name="ck_threat_indicator_type",
        ),
        sa.CheckConstraint(
            "severity IN ('low','medium','high','critical')",
            name="ck_threat_indicator_severity",
        ),
        sa.CheckConstraint(
            "status IN ('active','inactive','expired')",
            name="ck_threat_indicator_status",
        ),
        sa.CheckConstraint(
            "confidence IS NULL OR confidence BETWEEN 0 AND 100",
            name="ck_threat_indicator_confidence",
        ),
        sa.ForeignKeyConstraint(["feed_id"], ["threat_feeds.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "normalized_value", "indicator_type", name="uq_threat_indicator_value_type"
        ),
    )
    for name, col in (
        ("ix_threat_indicators_normalized_value", "normalized_value"),
        ("ix_threat_indicators_indicator_type", "indicator_type"),
        ("ix_threat_indicators_severity", "severity"),
        ("ix_threat_indicators_source", "source"),
        ("ix_threat_indicators_feed_id", "feed_id"),
        ("ix_threat_indicators_status", "status"),
        ("ix_threat_indicators_expires_at", "expires_at"),
    ):
        op.create_index(name, "threat_indicators", [col])

    op.create_table(
        "threat_feed_syncs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("feed_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("imported_count", sa.Integer(), nullable=False),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('queued','running','success','failed')",
            name="ck_threat_feed_sync_status",
        ),
        sa.ForeignKeyConstraint(["feed_id"], ["threat_feeds.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_threat_feed_syncs_feed_id", "threat_feed_syncs", ["feed_id"])
    op.create_index("ix_threat_feed_syncs_status", "threat_feed_syncs", ["status"])

    op.create_table(
        "threat_matches",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email_id", sa.Uuid(), nullable=False),
        sa.Column("detection_id", sa.Uuid(), nullable=True),
        sa.Column("indicator_id", sa.Uuid(), nullable=False),
        sa.Column("feed_id", sa.Uuid(), nullable=True),
        sa.Column("match_status", sa.String(20), nullable=False),
        sa.Column("matched_field", sa.String(40), nullable=False),
        sa.Column("matched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "match_status IN ('new','reviewed','investigating','resolved')",
            name="ck_threat_match_status",
        ),
        sa.ForeignKeyConstraint(["email_id"], ["emails.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["detection_id"], ["email_detections.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["indicator_id"], ["threat_indicators.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["feed_id"], ["threat_feeds.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "email_id", "indicator_id", name="uq_threat_match_email_indicator"
        ),
    )
    for name, col in (
        ("ix_threat_matches_email_id", "email_id"),
        ("ix_threat_matches_detection_id", "detection_id"),
        ("ix_threat_matches_indicator_id", "indicator_id"),
        ("ix_threat_matches_feed_id", "feed_id"),
        ("ix_threat_matches_match_status", "match_status"),
        ("ix_threat_matches_matched_at", "matched_at"),
    ):
        op.create_index(name, "threat_matches", [col])


def downgrade():
    for name in (
        "ix_threat_matches_matched_at",
        "ix_threat_matches_match_status",
        "ix_threat_matches_feed_id",
        "ix_threat_matches_indicator_id",
        "ix_threat_matches_detection_id",
        "ix_threat_matches_email_id",
    ):
        op.drop_index(name, table_name="threat_matches")
    op.drop_table("threat_matches")
    op.drop_index("ix_threat_feed_syncs_status", table_name="threat_feed_syncs")
    op.drop_index("ix_threat_feed_syncs_feed_id", table_name="threat_feed_syncs")
    op.drop_table("threat_feed_syncs")
    for name in (
        "ix_threat_indicators_expires_at",
        "ix_threat_indicators_status",
        "ix_threat_indicators_feed_id",
        "ix_threat_indicators_source",
        "ix_threat_indicators_severity",
        "ix_threat_indicators_indicator_type",
        "ix_threat_indicators_normalized_value",
    ):
        op.drop_index(name, table_name="threat_indicators")
    op.drop_table("threat_indicators")
    op.drop_index("ix_threat_feeds_sync_status", table_name="threat_feeds")
    op.drop_index("ix_threat_feeds_enabled", table_name="threat_feeds")
    op.drop_index("ix_threat_feeds_name", table_name="threat_feeds")
    op.drop_table("threat_feeds")
