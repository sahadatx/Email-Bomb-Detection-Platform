"""Create dataset validation run and issue tables.

Revision ID: f1a2b3c4d5e6
Revises: c306f8a1e921
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "c306f8a1e921"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dataset_validation_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("dataset_version_id", sa.Uuid(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
            server_default="running",
        ),
        sa.Column(
            "overall_status",
            sa.String(length=30),
            nullable=True,
        ),
        sa.Column(
            "total_checks",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "passed_checks",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "warning_checks",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "failed_checks",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "total_samples",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "error_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "warning_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "summary",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
        sa.Column(
            "policy_version",
            sa.String(length=50),
            nullable=False,
            server_default="1.0",
        ),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["dataset_version_id"],
            ["dataset_versions.id"],
            name="fk_validation_runs_version_id",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "status IN ('running', 'completed', 'failed')",
            name="ck_validation_runs_status",
        ),
        sa.CheckConstraint(
            "overall_status IS NULL OR "
            "overall_status IN ('passed', 'warning', 'failed')",
            name="ck_validation_runs_overall_status",
        ),
        sa.CheckConstraint(
            "total_checks >= 0 AND "
            "passed_checks >= 0 AND "
            "warning_checks >= 0 AND "
            "failed_checks >= 0",
            name="ck_validation_runs_check_counts",
        ),
        sa.CheckConstraint(
            "total_samples >= 0 AND "
            "error_count >= 0 AND "
            "warning_count >= 0",
            name="ck_validation_runs_issue_counts",
        ),
    )

    op.create_index(
        "ix_validation_runs_version_id",
        "dataset_validation_runs",
        ["dataset_version_id"],
    )
    op.create_index(
        "ix_validation_runs_status",
        "dataset_validation_runs",
        ["status"],
    )
    op.create_index(
        "ix_validation_runs_started_at",
        "dataset_validation_runs",
        ["started_at"],
    )
    op.create_index(
        "ix_validation_runs_version_started",
        "dataset_validation_runs",
        ["dataset_version_id", "started_at"],
    )

    op.create_table(
        "dataset_validation_issues",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("validation_run_id", sa.Uuid(), nullable=False),
        sa.Column("check_code", sa.String(length=100), nullable=False),
        sa.Column("check_name", sa.String(length=255), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("details", sa.Text(), nullable=False),
        sa.Column(
            "affected_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "affected_email_ids",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'"),
        ),
        sa.Column(
            "metadata_json",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["validation_run_id"],
            ["dataset_validation_runs.id"],
            name="fk_validation_issues_run_id",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "severity IN ('error', 'warning', 'info')",
            name="ck_validation_issues_severity",
        ),
        sa.CheckConstraint(
            "affected_count >= 0",
            name="ck_validation_issues_affected_count",
        ),
    )

    op.create_index(
        "ix_validation_issues_run_id",
        "dataset_validation_issues",
        ["validation_run_id"],
    )
    op.create_index(
        "ix_validation_issues_severity",
        "dataset_validation_issues",
        ["severity"],
    )
    op.create_index(
        "ix_validation_issues_run_severity",
        "dataset_validation_issues",
        ["validation_run_id", "severity"],
    )
    op.create_index(
        "ix_validation_issues_check_code",
        "dataset_validation_issues",
        ["check_code"],
    )


def downgrade() -> None:
    op.drop_table("dataset_validation_issues")
    op.drop_table("dataset_validation_runs")
