"""Align dataset management schema with Module 05 architecture.

Revision ID: c306f8a1e921
Revises: b205_add_dataset_sample_membership
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c306f8a1e921"
down_revision: Union[str, Sequence[str], None] = (
    "b205_add_dataset_sample_membership"
)
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. Align datasets with the Dataset model.
    # ------------------------------------------------------------------
    with op.batch_alter_table("datasets", recreate="always") as batch:
        batch.drop_column("source")
        batch.drop_column("label_source")
        batch.drop_column("label_schema")
        batch.drop_column("validate_samples")
        batch.drop_column("remove_duplicates")
        batch.drop_column("generate_version")
        batch.drop_column("current_version_id")

    # ------------------------------------------------------------------
    # 2. Rebuild dataset_samples as dataset-level sample selection.
    #    The previous version-scoped table is replaced.
    # ------------------------------------------------------------------
    op.drop_table("dataset_samples")

    op.create_table(
        "dataset_samples",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("dataset_id", sa.Uuid(), nullable=False),
        sa.Column("email_id", sa.Uuid(), nullable=False),
        sa.Column(
            "ground_truth",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "feature_schema_version",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["dataset_id"],
            ["datasets.id"],
            name="fk_dataset_samples_dataset_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["email_id"],
            ["emails.id"],
            name="fk_dataset_samples_email_id",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "dataset_id",
            "email_id",
            name="uq_dataset_sample_dataset_email",
        ),
        sa.CheckConstraint(
            "ground_truth IN ('normal', 'bombing')",
            name="ck_dataset_samples_ground_truth",
        ),
    )

    op.create_index(
        "ix_dataset_samples_dataset_id",
        "dataset_samples",
        ["dataset_id"],
    )
    op.create_index(
        "ix_dataset_samples_email_id",
        "dataset_samples",
        ["email_id"],
    )

    # ------------------------------------------------------------------
    # 3. Align dataset_versions with the DatasetVersion model.
    # ------------------------------------------------------------------
    with op.batch_alter_table(
        "dataset_versions",
        recreate="always",
    ) as batch:
        batch.alter_column(
            "version_label",
            new_column_name="name",
            existing_type=sa.String(length=50),
            existing_nullable=False,
        )
        batch.alter_column(
            "total_samples",
            new_column_name="sample_count",
            existing_type=sa.Integer(),
            existing_nullable=False,
        )
        batch.alter_column(
            "normal_samples",
            new_column_name="normal_count",
            existing_type=sa.Integer(),
            existing_nullable=False,
        )
        batch.alter_column(
            "bombing_samples",
            new_column_name="bombing_count",
            existing_type=sa.Integer(),
            existing_nullable=False,
        )

        batch.add_column(
            sa.Column(
                "training_percentage",
                sa.Integer(),
                nullable=False,
                server_default="70",
            )
        )
        batch.add_column(
            sa.Column(
                "validation_percentage",
                sa.Integer(),
                nullable=False,
                server_default="15",
            )
        )
        batch.add_column(
            sa.Column(
                "testing_percentage",
                sa.Integer(),
                nullable=False,
                server_default="15",
            )
        )
        batch.add_column(
            sa.Column(
                "random_seed",
                sa.Integer(),
                nullable=False,
                server_default="42",
            )
        )
        batch.add_column(
            sa.Column(
                "stratified",
                sa.Boolean(),
                nullable=False,
                server_default=sa.true(),
            )
        )
        batch.add_column(
            sa.Column(
                "training_count",
                sa.Integer(),
                nullable=False,
                server_default="0",
            )
        )
        batch.add_column(
            sa.Column(
                "validation_count",
                sa.Integer(),
                nullable=False,
                server_default="0",
            )
        )
        batch.add_column(
            sa.Column(
                "testing_count",
                sa.Integer(),
                nullable=False,
                server_default="0",
            )
        )
        batch.add_column(
            sa.Column(
                "validation_passed",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )
        batch.add_column(
            sa.Column(
                "feature_schema",
                sa.JSON(),
                nullable=False,
                server_default="{}",
            )
        )
        batch.add_column(
            sa.Column(
                "validated_at",
                sa.DateTime(timezone=True),
                nullable=True,
            )
        )

        batch.drop_column("change_summary")
        batch.drop_column("invalid_samples")
        batch.drop_column("duplicate_samples")
        batch.drop_column("split_summary")

        batch.create_check_constraint(
            "ck_dataset_version_training_percentage",
            "training_percentage >= 0 AND training_percentage <= 100",
        )
        batch.create_check_constraint(
            "ck_dataset_version_validation_percentage",
            "validation_percentage >= 0 AND validation_percentage <= 100",
        )
        batch.create_check_constraint(
            "ck_dataset_version_testing_percentage",
            "testing_percentage >= 0 AND testing_percentage <= 100",
        )
        batch.create_check_constraint(
            "ck_dataset_version_split_percentages",
            "training_percentage + validation_percentage "
            "+ testing_percentage = 100",
        )

    # ------------------------------------------------------------------
    # 4. Create version-level split membership.
    # ------------------------------------------------------------------
    op.create_table(
        "dataset_memberships",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("dataset_version_id", sa.Uuid(), nullable=False),
        sa.Column("email_id", sa.Uuid(), nullable=False),
        sa.Column("split", sa.String(length=50), nullable=False),
        sa.Column(
            "ground_truth",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "feature_schema_version",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["dataset_version_id"],
            ["dataset_versions.id"],
            name="fk_dataset_memberships_version_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["email_id"],
            ["emails.id"],
            name="fk_dataset_memberships_email_id",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "dataset_version_id",
            "email_id",
            name="uq_dataset_membership_version_email",
        ),
        sa.CheckConstraint(
            "split IN ('train', 'validation', 'test')",
            name="ck_dataset_memberships_split",
        ),
        sa.CheckConstraint(
            "ground_truth IN ('normal', 'bombing')",
            name="ck_dataset_memberships_ground_truth",
        ),
    )

    op.create_index(
        "ix_dataset_memberships_version_id",
        "dataset_memberships",
        ["dataset_version_id"],
    )
    op.create_index(
        "ix_dataset_memberships_email_id",
        "dataset_memberships",
        ["email_id"],
    )
    op.create_index(
        "ix_dataset_memberships_version_split",
        "dataset_memberships",
        ["dataset_version_id", "split"],
    )


def downgrade() -> None:
    # Remove the newly introduced membership table.
    op.drop_table("dataset_memberships")

    # Restore the old version-scoped dataset_samples schema.
    op.drop_table("dataset_samples")

    op.create_table(
        "dataset_samples",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("dataset_version_id", sa.Uuid(), nullable=False),
        sa.Column("email_id", sa.Uuid(), nullable=False),
        sa.Column("feature_record_id", sa.Uuid(), nullable=True),
        sa.Column("f1_sender_email", sa.String(length=320), nullable=True),
        sa.Column("f2_known_domain_indicator", sa.Boolean(), nullable=False),
        sa.Column("f3_message_id_presence", sa.Boolean(), nullable=False),
        sa.Column("f4_auto_submitted_header", sa.Boolean(), nullable=False),
        sa.Column("f5_precedence_bulk_indicator", sa.Boolean(), nullable=False),
        sa.Column("f6_list_id_header", sa.Boolean(), nullable=False),
        sa.Column("f7_x_beenthere_header", sa.Boolean(), nullable=False),
        sa.Column("f8_x_anti_abuse_header", sa.Boolean(), nullable=False),
        sa.Column("f9_keyword_content_features", sa.Integer(), nullable=False),
        sa.Column("f10_subject_length", sa.Integer(), nullable=False),
        sa.Column("f11_emails_per_minute", sa.Integer(), nullable=False),
        sa.Column("f12_emails_per_hour", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(length=50), nullable=False),
        sa.Column("validation_status", sa.String(length=50), nullable=False),
        sa.Column("validation_errors", sa.JSON(), nullable=True),
        sa.Column("validation_warnings", sa.JSON(), nullable=True),
        sa.Column("duplicate_group_id", sa.String(length=100), nullable=True),
        sa.Column("split", sa.String(length=50), nullable=True),
        sa.Column("feature_vector", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["dataset_version_id"],
            ["dataset_versions.id"],
            name="fk_dataset_samples_dataset_version_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["email_id"],
            ["emails.id"],
            name="fk_dataset_samples_email_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["feature_record_id"],
            ["email_features.id"],
            name="fk_dataset_samples_feature_record_id",
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint(
            "dataset_version_id",
            "email_id",
            name="uq_dataset_version_email",
        ),
    )

    with op.batch_alter_table(
        "dataset_versions",
        recreate="always",
    ) as batch:
        batch.drop_constraint(
            "ck_dataset_version_split_percentages",
            type_="check",
        )
        batch.drop_constraint(
            "ck_dataset_version_training_percentage",
            type_="check",
        )
        batch.drop_constraint(
            "ck_dataset_version_validation_percentage",
            type_="check",
        )
        batch.drop_constraint(
            "ck_dataset_version_testing_percentage",
            type_="check",
        )

        batch.drop_column("validated_at")
        batch.drop_column("feature_schema")
        batch.drop_column("validation_passed")
        batch.drop_column("testing_count")
        batch.drop_column("validation_count")
        batch.drop_column("training_count")
        batch.drop_column("stratified")
        batch.drop_column("random_seed")
        batch.drop_column("testing_percentage")
        batch.drop_column("validation_percentage")
        batch.drop_column("training_percentage")

        batch.alter_column(
            "name",
            new_column_name="version_label",
            existing_type=sa.String(length=50),
            existing_nullable=False,
        )
        batch.alter_column(
            "sample_count",
            new_column_name="total_samples",
            existing_type=sa.Integer(),
            existing_nullable=False,
        )
        batch.alter_column(
            "normal_count",
            new_column_name="normal_samples",
            existing_type=sa.Integer(),
            existing_nullable=False,
        )
        batch.alter_column(
            "bombing_count",
            new_column_name="bombing_samples",
            existing_type=sa.Integer(),
            existing_nullable=False,
        )

        batch.add_column(
            sa.Column("change_summary", sa.Text(), nullable=True)
        )
        batch.add_column(
            sa.Column(
                "invalid_samples",
                sa.Integer(),
                nullable=False,
                server_default="0",
            )
        )
        batch.add_column(
            sa.Column(
                "duplicate_samples",
                sa.Integer(),
                nullable=False,
                server_default="0",
            )
        )
        batch.add_column(
            sa.Column("split_summary", sa.JSON(), nullable=True)
        )

    with op.batch_alter_table("datasets", recreate="always") as batch:
        batch.add_column(
            sa.Column(
                "source",
                sa.String(length=50),
                nullable=False,
                server_default="MANUAL",
            )
        )
        batch.add_column(
            sa.Column(
                "label_source",
                sa.String(length=50),
                nullable=False,
                server_default="MANUAL",
            )
        )
        batch.add_column(
            sa.Column(
                "label_schema",
                sa.JSON(),
                nullable=False,
                server_default="{}",
            )
        )
        batch.add_column(
            sa.Column(
                "validate_samples",
                sa.Boolean(),
                nullable=False,
                server_default=sa.true(),
            )
        )
        batch.add_column(
            sa.Column(
                "remove_duplicates",
                sa.Boolean(),
                nullable=False,
                server_default=sa.true(),
            )
        )
        batch.add_column(
            sa.Column(
                "generate_version",
                sa.Boolean(),
                nullable=False,
                server_default=sa.true(),
            )
        )
        batch.add_column(
            sa.Column(
                "current_version_id",
                sa.Uuid(),
                nullable=True,
            )
        )
