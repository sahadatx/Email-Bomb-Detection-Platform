
"""add ml model management tables

Revision ID: e4cbb269b3ff
Revises: 32c402404546
Create Date: 2026-09-29 15:48:24.338780
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e4cbb269b3ff"
down_revision: Union[str, Sequence[str], None] = "32c402404546"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ml_model_definitions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("algorithm", sa.String(length=100), nullable=False),
        sa.Column("hyperparameters", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('active', 'inactive')",
            name="ck_ml_model_definitions_status",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ml_model_definitions_name",
        "ml_model_definitions",
        ["name"],
    )
    op.create_index(
        "ix_ml_model_definitions_algorithm",
        "ml_model_definitions",
        ["algorithm"],
    )
    op.create_index(
        "ix_ml_model_definitions_status",
        "ml_model_definitions",
        ["status"],
    )
    op.create_index(
        "ix_ml_model_definitions_created_at",
        "ml_model_definitions",
        ["created_at"],
    )

    op.create_table(
        "ml_training_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("model_definition_id", sa.Uuid(), nullable=False),
        sa.Column("preprocessing_run_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("progress_percent", sa.Integer(), nullable=False),
        sa.Column("config_snapshot", sa.JSON(), nullable=False),
        sa.Column("training_sample_count", sa.Integer(), nullable=False),
        sa.Column("validation_sample_count", sa.Integer(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("result_summary", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN "
            "('pending', 'queued', 'running', 'completed', "
            "'failed', 'cancelled')",
            name="ck_ml_training_runs_status",
        ),
        sa.CheckConstraint(
            "progress_percent >= 0 AND progress_percent <= 100 "
            "AND training_sample_count >= 0 "
            "AND validation_sample_count >= 0 "
            "AND (duration_ms IS NULL OR duration_ms >= 0)",
            name="ck_ml_training_runs_counts",
        ),
        sa.ForeignKeyConstraint(
            ["model_definition_id"],
            ["ml_model_definitions.id"],
            name="fk_ml_training_runs_model_definition_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["preprocessing_run_id"],
            ["preprocessing_runs.id"],
            name="fk_ml_training_runs_preprocessing_run_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ml_training_runs_model_definition_id",
        "ml_training_runs",
        ["model_definition_id"],
    )
    op.create_index(
        "ix_ml_training_runs_preprocessing_run_id",
        "ml_training_runs",
        ["preprocessing_run_id"],
    )
    op.create_index(
        "ix_ml_training_runs_status",
        "ml_training_runs",
        ["status"],
    )
    op.create_index(
        "ix_ml_training_runs_created_at",
        "ml_training_runs",
        ["created_at"],
    )
    op.create_index(
        "ix_ml_training_runs_model_created",
        "ml_training_runs",
        ["model_definition_id", "created_at"],
    )

    op.create_table(
        "ml_model_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("model_definition_id", sa.Uuid(), nullable=False),
        sa.Column("training_run_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("artifact_filename", sa.String(length=255), nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("media_type", sa.String(length=150), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "version > 0 AND size_bytes >= 0",
            name="ck_ml_model_versions_values",
        ),
        sa.CheckConstraint(
            "status IN ('registered', 'active', 'archived')",
            name="ck_ml_model_versions_status",
        ),
        sa.ForeignKeyConstraint(
            ["model_definition_id"],
            ["ml_model_definitions.id"],
            name="fk_ml_model_versions_model_definition_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["training_run_id"],
            ["ml_training_runs.id"],
            name="fk_ml_model_versions_training_run_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "training_run_id",
            name="uq_ml_model_versions_training_run_id",
        ),
        sa.UniqueConstraint(
            "model_definition_id",
            "version",
            name="uq_ml_model_versions_definition_version",
        ),
    )
    op.create_index(
        "ix_ml_model_versions_definition_id",
        "ml_model_versions",
        ["model_definition_id"],
    )
    op.create_index(
        "ix_ml_model_versions_training_run_id",
        "ml_model_versions",
        ["training_run_id"],
    )
    op.create_index(
        "ix_ml_model_versions_status",
        "ml_model_versions",
        ["status"],
    )
    op.create_index(
        "ix_ml_model_versions_created_at",
        "ml_model_versions",
        ["created_at"],
    )

    op.create_table(
        "ml_evaluation_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("model_version_id", sa.Uuid(), nullable=False),
        sa.Column("preprocessing_run_id", sa.Uuid(), nullable=False),
        sa.Column("evaluation_split", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("sample_count", sa.Integer(), nullable=False),
        sa.Column("accuracy", sa.Float(), nullable=True),
        sa.Column("precision", sa.Float(), nullable=True),
        sa.Column("recall", sa.Float(), nullable=True),
        sa.Column("f1_score", sa.Float(), nullable=True),
        sa.Column("roc_auc", sa.Float(), nullable=True),
        sa.Column("confusion_matrix", sa.JSON(), nullable=False),
        sa.Column("classification_report", sa.JSON(), nullable=False),
        sa.Column("result_summary", sa.JSON(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "evaluation_split IN ('validation', 'testing')",
            name="ck_ml_evaluation_runs_split",
        ),
        sa.CheckConstraint(
            "status IN "
            "('pending', 'running', 'completed', 'failed', 'cancelled')",
            name="ck_ml_evaluation_runs_status",
        ),
        sa.CheckConstraint(
            "sample_count >= 0 "
            "AND (duration_ms IS NULL OR duration_ms >= 0)",
            name="ck_ml_evaluation_runs_counts",
        ),
        sa.CheckConstraint(
            "(accuracy IS NULL OR (accuracy >= 0 AND accuracy <= 1)) "
            "AND (precision IS NULL OR (precision >= 0 AND precision <= 1)) "
            "AND (recall IS NULL OR (recall >= 0 AND recall <= 1)) "
            "AND (f1_score IS NULL OR (f1_score >= 0 AND f1_score <= 1)) "
            "AND (roc_auc IS NULL OR (roc_auc >= 0 AND roc_auc <= 1))",
            name="ck_ml_evaluation_runs_metrics",
        ),
        sa.ForeignKeyConstraint(
            ["model_version_id"],
            ["ml_model_versions.id"],
            name="fk_ml_evaluation_runs_model_version_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["preprocessing_run_id"],
            ["preprocessing_runs.id"],
            name="fk_ml_evaluation_runs_preprocessing_run_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ml_evaluation_runs_model_version_id",
        "ml_evaluation_runs",
        ["model_version_id"],
    )
    op.create_index(
        "ix_ml_evaluation_runs_preprocessing_run_id",
        "ml_evaluation_runs",
        ["preprocessing_run_id"],
    )
    op.create_index(
        "ix_ml_evaluation_runs_status",
        "ml_evaluation_runs",
        ["status"],
    )
    op.create_index(
        "ix_ml_evaluation_runs_created_at",
        "ml_evaluation_runs",
        ["created_at"],
    )
    op.create_index(
        "ix_ml_evaluation_runs_version_created",
        "ml_evaluation_runs",
        ["model_version_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_ml_evaluation_runs_version_created",
        table_name="ml_evaluation_runs",
    )
    op.drop_index(
        "ix_ml_evaluation_runs_created_at",
        table_name="ml_evaluation_runs",
    )
    op.drop_index(
        "ix_ml_evaluation_runs_status",
        table_name="ml_evaluation_runs",
    )
    op.drop_index(
        "ix_ml_evaluation_runs_preprocessing_run_id",
        table_name="ml_evaluation_runs",
    )
    op.drop_index(
        "ix_ml_evaluation_runs_model_version_id",
        table_name="ml_evaluation_runs",
    )
    op.drop_table("ml_evaluation_runs")

    op.drop_index(
        "ix_ml_model_versions_created_at",
        table_name="ml_model_versions",
    )
    op.drop_index(
        "ix_ml_model_versions_status",
        table_name="ml_model_versions",
    )
    op.drop_index(
        "ix_ml_model_versions_training_run_id",
        table_name="ml_model_versions",
    )
    op.drop_index(
        "ix_ml_model_versions_definition_id",
        table_name="ml_model_versions",
    )
    op.drop_table("ml_model_versions")

    op.drop_index(
        "ix_ml_training_runs_model_created",
        table_name="ml_training_runs",
    )
    op.drop_index(
        "ix_ml_training_runs_created_at",
        table_name="ml_training_runs",
    )
    op.drop_index(
        "ix_ml_training_runs_status",
        table_name="ml_training_runs",
    )
    op.drop_index(
        "ix_ml_training_runs_preprocessing_run_id",
        table_name="ml_training_runs",
    )
    op.drop_index(
        "ix_ml_training_runs_model_definition_id",
        table_name="ml_training_runs",
    )
    op.drop_table("ml_training_runs")

    op.drop_index(
        "ix_ml_model_definitions_created_at",
        table_name="ml_model_definitions",
    )
    op.drop_index(
        "ix_ml_model_definitions_status",
        table_name="ml_model_definitions",
    )
    op.drop_index(
        "ix_ml_model_definitions_algorithm",
        table_name="ml_model_definitions",
    )
    op.drop_index(
        "ix_ml_model_definitions_name",
        table_name="ml_model_definitions",
    )
    op.drop_table("ml_model_definitions")
