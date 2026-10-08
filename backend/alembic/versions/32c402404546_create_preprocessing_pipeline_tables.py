"""create preprocessing pipeline tables

Revision ID: 32c402404546
Revises: f1a2b3c4d5e6
Create Date: 2026-09-28 14:43:14.111005
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "32c402404546"
down_revision: Union[str, Sequence[str], None] = "f1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create preprocessing pipeline tables."""

    op.create_table(
        "preprocessing_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("dataset_version_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("config_snapshot", sa.JSON(), nullable=False),
        sa.Column("input_sample_count", sa.Integer(), nullable=False),
        sa.Column("output_sample_count", sa.Integer(), nullable=False),
        sa.Column("training_count", sa.Integer(), nullable=False),
        sa.Column("validation_count", sa.Integer(), nullable=False),
        sa.Column("testing_count", sa.Integer(), nullable=False),
        sa.Column("feature_count", sa.Integer(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("result_summary", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed')",
            name="ck_preprocessing_runs_status",
        ),
        sa.CheckConstraint(
            "input_sample_count >= 0 "
            "AND output_sample_count >= 0 "
            "AND training_count >= 0 "
            "AND validation_count >= 0 "
            "AND testing_count >= 0 "
            "AND feature_count >= 0 "
            "AND (duration_ms IS NULL OR duration_ms >= 0)",
            name="ck_preprocessing_runs_counts",
        ),
        sa.ForeignKeyConstraint(
            ["dataset_version_id"],
            ["dataset_versions.id"],
            name="fk_preprocessing_runs_dataset_version_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_preprocessing_runs_created_at",
        "preprocessing_runs",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_preprocessing_runs_dataset_version_id",
        "preprocessing_runs",
        ["dataset_version_id"],
        unique=False,
    )
    op.create_index(
        "ix_preprocessing_runs_status",
        "preprocessing_runs",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_preprocessing_runs_version_created",
        "preprocessing_runs",
        ["dataset_version_id", "created_at"],
        unique=False,
    )

    op.create_table(
        "preprocessing_artifacts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("preprocessing_run_id", sa.Uuid(), nullable=False),
        sa.Column("artifact_type", sa.String(length=50), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("media_type", sa.String(length=150), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "size_bytes >= 0",
            name="ck_preprocessing_artifacts_size",
        ),
        sa.ForeignKeyConstraint(
            ["preprocessing_run_id"],
            ["preprocessing_runs.id"],
            name="fk_preprocessing_artifacts_run_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "preprocessing_run_id",
            "artifact_type",
            name="uq_preprocessing_artifacts_run_type",
        ),
    )

    op.create_index(
        "ix_preprocessing_artifacts_run_id",
        "preprocessing_artifacts",
        ["preprocessing_run_id"],
        unique=False,
    )
    op.create_index(
        "ix_preprocessing_artifacts_type",
        "preprocessing_artifacts",
        ["artifact_type"],
        unique=False,
    )


def downgrade() -> None:
    """Drop preprocessing pipeline tables."""

    op.drop_index(
        "ix_preprocessing_artifacts_type",
        table_name="preprocessing_artifacts",
    )
    op.drop_index(
        "ix_preprocessing_artifacts_run_id",
        table_name="preprocessing_artifacts",
    )
    op.drop_table("preprocessing_artifacts")

    op.drop_index(
        "ix_preprocessing_runs_version_created",
        table_name="preprocessing_runs",
    )
    op.drop_index(
        "ix_preprocessing_runs_status",
        table_name="preprocessing_runs",
    )
    op.drop_index(
        "ix_preprocessing_runs_dataset_version_id",
        table_name="preprocessing_runs",
    )
    op.drop_index(
        "ix_preprocessing_runs_created_at",
        table_name="preprocessing_runs",
    )
    op.drop_table("preprocessing_runs")
