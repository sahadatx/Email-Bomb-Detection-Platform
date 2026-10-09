
"""Add dataset sample membership and dataset counters.

Revision ID: b205_add_dataset_sample_membership
Revises: a194ca104bf8
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "b205_add_dataset_sample_membership"
down_revision = "a194ca104bf8"
branch_labels = None
depends_on = None


def _columns(table_name: str) -> set[str]:
    """Return existing column names for a table."""
    inspector = sa.inspect(op.get_bind())

    if table_name not in inspector.get_table_names():
        return set()

    return {
        column["name"]
        for column in inspector.get_columns(table_name)
    }


def _tables() -> set[str]:
    """Return existing database table names."""
    return set(
        sa.inspect(op.get_bind()).get_table_names()
    )


def upgrade() -> None:
    bind = op.get_bind()
    existing_tables = _tables()

    # --------------------------------------------------------
    # DATASET SUMMARY COLUMNS
    # --------------------------------------------------------

    if "datasets" not in existing_tables:
        raise RuntimeError(
            "The datasets table does not exist. "
            "Run the earlier migrations before this migration."
        )

    dataset_columns = _columns("datasets")

    with op.batch_alter_table(
        "datasets",
        recreate="auto",
    ) as batch_op:
        if "sample_count" not in dataset_columns:
            batch_op.add_column(
                sa.Column(
                    "sample_count",
                    sa.Integer(),
                    nullable=False,
                    server_default="0",
                )
            )

        if "normal_count" not in dataset_columns:
            batch_op.add_column(
                sa.Column(
                    "normal_count",
                    sa.Integer(),
                    nullable=False,
                    server_default="0",
                )
            )

        if "bombing_count" not in dataset_columns:
            batch_op.add_column(
                sa.Column(
                    "bombing_count",
                    sa.Integer(),
                    nullable=False,
                    server_default="0",
                )
            )

        if "feature_schema" not in dataset_columns:
            batch_op.add_column(
                sa.Column(
                    "feature_schema",
                    sa.String(length=32),
                    nullable=False,
                    server_default="F1-F12",
                )
            )

    # --------------------------------------------------------
    # DATASET-LEVEL SAMPLE MEMBERSHIP
    # --------------------------------------------------------
    #
    # Stores the exact email samples selected when a Dataset
    # is created. This is separate from version-level
    # DatasetMembership.
    #
    # Existing Dataset records remain intact.
    # --------------------------------------------------------

    if "dataset_samples" not in existing_tables:
        op.create_table(
            "dataset_samples",
            sa.Column(
                "id",
                sa.Uuid(),
                nullable=False,
            ),
            sa.Column(
                "dataset_id",
                sa.Uuid(),
                nullable=False,
            ),
            sa.Column(
                "email_id",
                sa.Uuid(),
                nullable=False,
            ),
            sa.Column(
                "ground_truth",
                sa.String(length=32),
                nullable=False,
            ),
            sa.Column(
                "feature_schema_version",
                sa.String(length=32),
                nullable=False,
                server_default="F1-F12",
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.ForeignKeyConstraint(
                ["dataset_id"],
                ["datasets.id"],
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["email_id"],
                ["emails.id"],
                ondelete="RESTRICT",
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "dataset_id",
                "email_id",
                name="uq_dataset_samples_dataset_email",
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
            unique=False,
        )

        op.create_index(
            "ix_dataset_samples_email_id",
            "dataset_samples",
            ["email_id"],
            unique=False,
        )

    # --------------------------------------------------------
    # EXISTING VERSION MEMBERSHIP INDEXES
    # --------------------------------------------------------

    if "dataset_memberships" in existing_tables:
        membership_indexes = {
            index["name"]
            for index in sa.inspect(bind).get_indexes(
                "dataset_memberships"
            )
        }

        if "ix_dataset_memberships_version_id" not in membership_indexes:
            op.create_index(
                "ix_dataset_memberships_version_id",
                "dataset_memberships",
                ["dataset_version_id"],
                unique=False,
            )


def downgrade() -> None:
    """
    Reverse the schema additions.

    The dataset_samples table is removed on downgrade.
    Any rows created in that table after upgrade will be lost.
    """

    existing_tables = _tables()

    if "dataset_memberships" in existing_tables:
        membership_indexes = {
            index["name"]
            for index in sa.inspect(op.get_bind()).get_indexes(
                "dataset_memberships"
            )
        }

        if "ix_dataset_memberships_version_id" in membership_indexes:
            op.drop_index(
                "ix_dataset_memberships_version_id",
                table_name="dataset_memberships",
            )

    if "dataset_samples" in existing_tables:
        op.drop_table("dataset_samples")

    if "datasets" in existing_tables:
        dataset_columns = _columns("datasets")

        with op.batch_alter_table(
            "datasets",
            recreate="auto",
        ) as batch_op:
            for column_name in (
                "feature_schema",
                "bombing_count",
                "normal_count",
                "sample_count",
            ):
                if column_name in dataset_columns:
                    batch_op.drop_column(column_name)
