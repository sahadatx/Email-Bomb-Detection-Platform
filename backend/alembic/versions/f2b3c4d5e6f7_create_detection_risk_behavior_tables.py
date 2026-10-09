"""create detection, risk, behavior, and detection settings tables

Revision ID: f2b3c4d5e6f7
Revises: e4cbb269b3ff
Create Date: 2026-09-30
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f2b3c4d5e6f7"
down_revision: Union[str, Sequence[str], None] = "e4cbb269b3ff"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "detection_inputs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("raw_content", sa.Text(), nullable=False),
        sa.Column("sender", sa.String(512), nullable=True),
        sa.Column("subject", sa.String(1024), nullable=True),
        sa.Column("feature_snapshot", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "email_detections",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email_id", sa.Uuid(), nullable=True),
        sa.Column("input_id", sa.Uuid(), nullable=True),
        sa.Column("model_version_id", sa.Uuid(), nullable=False),
        sa.Column("predicted_label", sa.String(20), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("feature_snapshot", sa.JSON(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("(email_id IS NOT NULL AND input_id IS NULL) OR (email_id IS NULL AND input_id IS NOT NULL)", name="ck_email_detections_single_input"),
        sa.ForeignKeyConstraint(["email_id"], ["emails.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["input_id"], ["detection_inputs.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["model_version_id"], ["ml_model_versions.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_email_detections_email_id", "email_detections", ["email_id"])
    op.create_index("ix_email_detections_input_id", "email_detections", ["input_id"])
    op.create_index("ix_email_detections_model_version_id", "email_detections", ["model_version_id"])
    op.create_index("ix_email_detections_predicted_label", "email_detections", ["predicted_label"])
    op.create_index("ix_email_detections_status", "email_detections", ["status"])
    op.create_index("ix_email_detections_created_at", "email_detections", ["created_at"])
    op.create_table(
        "detection_risk_assessments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("detection_id", sa.Uuid(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("level", sa.String(20), nullable=False),
        sa.Column("factors", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["detection_id"], ["email_detections.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("detection_id"),
    )
    op.create_index("ix_detection_risk_assessments_detection_id", "detection_risk_assessments", ["detection_id"])
    op.create_index("ix_detection_risk_assessments_level", "detection_risk_assessments", ["level"])
    op.create_table(
        "detection_behavioral_results",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("detection_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("anomalies", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["detection_id"], ["email_detections.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("detection_id"),
    )
    op.create_index("ix_detection_behavioral_results_detection_id", "detection_behavioral_results", ["detection_id"])
    op.create_table(
        "detection_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("high_risk_threshold", sa.Integer(), nullable=False),
        sa.Column("critical_risk_threshold", sa.Integer(), nullable=False),
        sa.Column("enable_behavioral_analysis", sa.Boolean(), nullable=False),
        sa.Column("save_feature_snapshots", sa.Boolean(), nullable=False),
        sa.Column("store_detection_history", sa.Boolean(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("id = 1", name="ck_detection_settings_singleton"),
        sa.CheckConstraint("high_risk_threshold BETWEEN 1 AND 100", name="ck_detection_settings_high_threshold"),
        sa.CheckConstraint("critical_risk_threshold BETWEEN 1 AND 100", name="ck_detection_settings_critical_threshold"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("detection_settings")
    op.drop_index("ix_detection_behavioral_results_detection_id", table_name="detection_behavioral_results")
    op.drop_table("detection_behavioral_results")
    op.drop_index("ix_detection_risk_assessments_level", table_name="detection_risk_assessments")
    op.drop_index("ix_detection_risk_assessments_detection_id", table_name="detection_risk_assessments")
    op.drop_table("detection_risk_assessments")
    for name in ("ix_email_detections_created_at", "ix_email_detections_status", "ix_email_detections_predicted_label", "ix_email_detections_model_version_id", "ix_email_detections_input_id", "ix_email_detections_email_id"):
        op.drop_index(name, table_name="email_detections")
    op.drop_table("email_detections")
    op.drop_table("detection_inputs")
