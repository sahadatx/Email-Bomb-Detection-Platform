"""Create persisted experiment definitions and orchestrator runs.

Revision ID: f7a8b9c0d1e2
Revises: e6f7a8b9c0d1
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "f7a8b9c0d1e2"
down_revision = "e6f7a8b9c0d1"
branch_labels = None
depends_on = None


def uuid_type():
    return sa.Uuid(as_uuid=True)


def json_type():
    return sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.create_table(
        "experiments",
        sa.Column("id", uuid_type(), primary_key=True, nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("name", sa.String(180), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("model_definition_id", uuid_type(), sa.ForeignKey("ml_model_definitions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("dataset_version_id", uuid_type(), sa.ForeignKey("dataset_versions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("preprocessing_run_id", uuid_type(), sa.ForeignKey("preprocessing_runs.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("feature_set_snapshot", json_type(), nullable=False),
        sa.Column("training_config", json_type(), nullable=False),
        sa.Column("evaluation_config", json_type(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("created_by_id", uuid_type(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('draft','queued','running','completed','failed','cancelled')", name="ck_experiments_status"),
    )
    op.create_index("ix_experiments_code", "experiments", ["code"], unique=True)
    for column in ("name", "model_definition_id", "dataset_version_id", "preprocessing_run_id", "status", "created_by_id", "created_at"):
        op.create_index(f"ix_experiments_{column}", "experiments", [column])
    op.create_index("ix_experiments_dataset_model", "experiments", ["dataset_version_id", "model_definition_id"])

    op.create_table(
        "experiment_runs",
        sa.Column("id", uuid_type(), primary_key=True, nullable=False),
        sa.Column("experiment_id", uuid_type(), sa.ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("training_run_id", uuid_type(), sa.ForeignKey("ml_training_runs.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("evaluation_run_id", uuid_type(), sa.ForeignKey("ml_evaluation_runs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("progress_percent", sa.Integer(), nullable=False),
        sa.Column("logs", json_type(), nullable=False),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('queued','running','completed','failed','cancelled')", name="ck_experiment_runs_status"),
        sa.CheckConstraint("progress_percent BETWEEN 0 AND 100", name="ck_experiment_runs_progress"),
    )
    op.create_index("ix_experiment_runs_experiment_id", "experiment_runs", ["experiment_id"])
    op.create_index("ix_experiment_runs_training_run_id", "experiment_runs", ["training_run_id"], unique=True)
    op.create_index("ix_experiment_runs_evaluation_run_id", "experiment_runs", ["evaluation_run_id"], unique=True)
    op.create_index("ix_experiment_runs_status", "experiment_runs", ["status"])
    op.create_index("ix_experiment_runs_created_at", "experiment_runs", ["created_at"])


def downgrade() -> None:
    op.drop_table("experiment_runs")
    op.drop_table("experiments")
