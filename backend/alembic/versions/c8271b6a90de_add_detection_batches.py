"""Persist grouped email detection submissions.

Revision ID: c8271b6a90de
Revises: f1e2d3c4b5a6
"""

from alembic import op
import sqlalchemy as sa

revision = "c8271b6a90de"
down_revision = "f1e2d3c4b5a6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "detection_batches",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("total_count", sa.Integer(), nullable=False),
        sa.Column("succeeded_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("detection_inputs") as batch:
        batch.add_column(sa.Column("batch_id", sa.Uuid(), nullable=True))
        batch.create_foreign_key("fk_detection_inputs_batch_id", "detection_batches", ["batch_id"], ["id"], ondelete="SET NULL")
        batch.create_index("ix_detection_inputs_batch_id", ["batch_id"])
    with op.batch_alter_table("email_detections") as batch:
        batch.add_column(sa.Column("batch_id", sa.Uuid(), nullable=True))
        batch.create_foreign_key("fk_email_detections_batch_id", "detection_batches", ["batch_id"], ["id"], ondelete="SET NULL")
        batch.create_index("ix_email_detections_batch_id", ["batch_id"])


def downgrade() -> None:
    with op.batch_alter_table("email_detections") as batch:
        batch.drop_index("ix_email_detections_batch_id")
        batch.drop_constraint("fk_email_detections_batch_id", type_="foreignkey")
        batch.drop_column("batch_id")
    with op.batch_alter_table("detection_inputs") as batch:
        batch.drop_index("ix_detection_inputs_batch_id")
        batch.drop_constraint("fk_detection_inputs_batch_id", type_="foreignkey")
        batch.drop_column("batch_id")
    op.drop_table("detection_batches")
