"""create explainability notes, evidence workflow, and reports

Revision ID: a7b8c9d0e1f2
Revises: f4c5d6e7a8b9
Create Date: 2026-09-30
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a7b8c9d0e1f2"
down_revision: Union[str, Sequence[str], None] = "f4c5d6e7a8b9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "investigation_evidence",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("detection_id", sa.Uuid(), nullable=False),
        sa.Column("source_email_id", sa.Uuid(), nullable=True),
        sa.Column("evidence_type", sa.String(32), nullable=False),
        sa.Column("name", sa.String(240), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("observed_value", sa.Text(), nullable=True),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("review_status", sa.String(24), nullable=False),
        sa.Column("analyst_note", sa.Text(), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(36), nullable=False),
        sa.Column("updated_by", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["detection_id"], ["email_detections.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["source_email_id"], ["emails.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_investigation_evidence_detection_id", "investigation_evidence", ["detection_id"])
    op.create_index("ix_investigation_evidence_source_email_id", "investigation_evidence", ["source_email_id"])
    op.create_index("ix_investigation_evidence_evidence_type", "investigation_evidence", ["evidence_type"])
    op.create_index("ix_investigation_evidence_review_status", "investigation_evidence", ["review_status"])
    op.create_index("ix_investigation_evidence_created_by", "investigation_evidence", ["created_by"])
    op.create_index("ix_investigation_evidence_created", "investigation_evidence", ["created_at"])

    op.create_table(
        "investigation_evidence_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("evidence_id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.String(36), nullable=False),
        sa.Column("action", sa.String(32), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("before_data", sa.JSON(), nullable=False),
        sa.Column("after_data", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["evidence_id"], ["investigation_evidence.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_investigation_evidence_events_evidence_id", "investigation_evidence_events", ["evidence_id"])
    op.create_index("ix_investigation_evidence_events_created_at", "investigation_evidence_events", ["created_at"])

    op.create_table(
        "detection_analyst_notes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("detection_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(240), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("category", sa.String(24), nullable=False),
        sa.Column("author_id", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["detection_id"], ["email_detections.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_detection_analyst_notes_detection_id", "detection_analyst_notes", ["detection_id"])
    op.create_index("ix_detection_analyst_notes_author_id", "detection_analyst_notes", ["author_id"])

    op.create_table(
        "investigation_reports",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("report_type", sa.String(24), nullable=False),
        sa.Column("output_format", sa.String(12), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("detection_ids", sa.JSON(), nullable=False),
        sa.Column("sections", sa.JSON(), nullable=False),
        sa.Column("analyst_notes", sa.Text(), nullable=True),
        sa.Column("configuration", sa.JSON(), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=True),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_investigation_reports_title", "investigation_reports", ["title"])
    op.create_index("ix_investigation_reports_report_type", "investigation_reports", ["report_type"])
    op.create_index("ix_investigation_reports_status", "investigation_reports", ["status"])
    op.create_index("ix_investigation_reports_created_by", "investigation_reports", ["created_by"])

    op.create_table(
        "investigation_report_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("report_id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.String(36), nullable=False),
        sa.Column("action", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["report_id"], ["investigation_reports.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_investigation_report_events_report_id", "investigation_report_events", ["report_id"])
    op.create_index("ix_investigation_report_events_created_at", "investigation_report_events", ["created_at"])


def downgrade() -> None:
    op.drop_table("investigation_report_events")
    op.drop_table("investigation_reports")
    op.drop_table("detection_analyst_notes")
    op.drop_table("investigation_evidence_events")
    op.drop_table("investigation_evidence")
