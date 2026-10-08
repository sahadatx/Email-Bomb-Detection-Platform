"""create dataset management tables

Revision ID: 0f587db84483
Revises: daba77b99f58
Create Date: 2026-09-25
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# ---------------------------------------------------------------------------
# Revision identifiers
# ---------------------------------------------------------------------------

revision: str = "0f587db84483"
down_revision: Union[str, Sequence[str], None] = "daba77b99f58"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ---------------------------------------------------------------------------
# Upgrade
# ---------------------------------------------------------------------------


def upgrade() -> None:
    """
    Create Dataset Management tables.

    SQLite compatibility:
    - No ALTER TABLE ADD CONSTRAINT is used.
    - current_version_id is intentionally stored as a UUID reference
      without a database-level FK because it creates a circular dependency
      between datasets and dataset_versions.
    """

    # =======================================================================
    # 1. datasets
    # =======================================================================

    op.create_table(
        "datasets",

        # Primary key
        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
        ),

        # Basic metadata
        sa.Column(
            "name",
            sa.String(length=255),
            nullable=False,
        ),

        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
        ),

        # Dataset source
        sa.Column(
            "source",
            sa.String(length=50),
            nullable=False,
        ),

        # Ground-truth label source
        sa.Column(
            "label_source",
            sa.String(length=50),
            nullable=False,
        ),

        # Dataset lifecycle status
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
        ),

        # Allowed dataset labels
        sa.Column(
            "label_schema",
            sa.JSON(),
            nullable=False,
        ),

        # F1-F12 feature schema
        sa.Column(
            "feature_schema",
            sa.JSON(),
            nullable=False,
        ),

        # Dataset build options
        sa.Column(
            "validate_samples",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),

        sa.Column(
            "remove_duplicates",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),

        sa.Column(
            "generate_version",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),

        # -------------------------------------------------------------------
        # Current version reference
        #
        # Intentionally NOT a database FK.
        #
        # Reason:
        # datasets → dataset_versions
        # dataset_versions → datasets
        #
        # SQLite does not support adding this circular FK with ALTER TABLE.
        # The application service/repository layer validates this reference.
        # -------------------------------------------------------------------

        sa.Column(
            "current_version_id",
            sa.Uuid(),
            nullable=True,
        ),

        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),

        sa.PrimaryKeyConstraint("id"),
    )

    # Dataset name lookup
    op.create_index(
        "ix_datasets_name",
        "datasets",
        ["name"],
        unique=False,
    )

    # Dataset status filtering
    op.create_index(
        "ix_datasets_status",
        "datasets",
        ["status"],
        unique=False,
    )

    # =======================================================================
    # 2. dataset_versions
    # =======================================================================

    op.create_table(
        "dataset_versions",

        # Primary key
        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
        ),

        # Parent dataset
        sa.Column(
            "dataset_id",
            sa.Uuid(),
            nullable=False,
        ),

        # Version number
        sa.Column(
            "version_number",
            sa.Integer(),
            nullable=False,
        ),

        # Human-readable version
        sa.Column(
            "version_label",
            sa.String(length=50),
            nullable=False,
        ),

        # Version change description
        sa.Column(
            "change_summary",
            sa.Text(),
            nullable=True,
        ),

        # Sample statistics
        sa.Column(
            "total_samples",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),

        sa.Column(
            "valid_samples",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),

        sa.Column(
            "invalid_samples",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),

        sa.Column(
            "duplicate_samples",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),

        # Label distribution
        sa.Column(
            "normal_samples",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),

        sa.Column(
            "bombing_samples",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),

        # Version lifecycle status
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
        ),

        # Validation metadata
        sa.Column(
            "validation_summary",
            sa.JSON(),
            nullable=True,
        ),

        # Split metadata
        sa.Column(
            "split_summary",
            sa.JSON(),
            nullable=True,
        ),

        # Timestamp
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),

        sa.PrimaryKeyConstraint("id"),

        # Parent dataset FK
        sa.ForeignKeyConstraint(
            ["dataset_id"],
            ["datasets.id"],
            name="fk_dataset_versions_dataset_id",
            ondelete="CASCADE",
        ),

        # One version number per dataset
        sa.UniqueConstraint(
            "dataset_id",
            "version_number",
            name="uq_dataset_version_number",
        ),
    )

    # Parent dataset lookup
    op.create_index(
        "ix_dataset_versions_dataset_id",
        "dataset_versions",
        ["dataset_id"],
        unique=False,
    )

    # Version status filtering
    op.create_index(
        "ix_dataset_versions_status",
        "dataset_versions",
        ["status"],
        unique=False,
    )

    # Dataset + status filtering
    op.create_index(
        "ix_dataset_versions_dataset_status",
        "dataset_versions",
        ["dataset_id", "status"],
        unique=False,
    )

    # =======================================================================
    # 3. dataset_samples
    # =======================================================================

    op.create_table(
        "dataset_samples",

        # Primary key
        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
        ),

        # Parent dataset version
        sa.Column(
            "dataset_version_id",
            sa.Uuid(),
            nullable=False,
        ),

        # Original collected email
        sa.Column(
            "email_id",
            sa.Uuid(),
            nullable=False,
        ),

        # Module 04 feature record
        sa.Column(
            "feature_record_id",
            sa.Uuid(),
            nullable=True,
        ),

        # ===================================================================
        # F1 — F12
        # ===================================================================

        # F1
        sa.Column(
            "f1_sender_email",
            sa.String(length=320),
            nullable=True,
        ),

        # F2
        sa.Column(
            "f2_known_domain_indicator",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),

        # F3
        sa.Column(
            "f3_message_id_presence",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),

        # F4
        sa.Column(
            "f4_auto_submitted_header",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),

        # F5
        sa.Column(
            "f5_precedence_bulk_indicator",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),

        # F6
        sa.Column(
            "f6_list_id_header",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),

        # F7
        sa.Column(
            "f7_x_beenthere_header",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),

        # F8
        sa.Column(
            "f8_x_anti_abuse_header",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),

        # F9
        sa.Column(
            "f9_keyword_content_features",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),

        # F10
        sa.Column(
            "f10_subject_length",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),

        # F11
        sa.Column(
            "f11_emails_per_minute",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),

        # F12
        sa.Column(
            "f12_emails_per_hour",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),

        # ===================================================================
        # Ground Truth Label
        # ===================================================================

        sa.Column(
            "label",
            sa.String(length=50),
            nullable=False,
        ),

        # ===================================================================
        # Validation
        # ===================================================================

        sa.Column(
            "validation_status",
            sa.String(length=50),
            nullable=False,
            server_default="PENDING",
        ),

        sa.Column(
            "validation_errors",
            sa.JSON(),
            nullable=True,
        ),

        sa.Column(
            "validation_warnings",
            sa.JSON(),
            nullable=True,
        ),

        # ===================================================================
        # Deduplication
        # ===================================================================

        sa.Column(
            "duplicate_group_id",
            sa.String(length=100),
            nullable=True,
        ),

        # ===================================================================
        # Dataset split
        # ===================================================================

        sa.Column(
            "split",
            sa.String(length=50),
            nullable=True,
        ),

        # ===================================================================
        # Reproducible feature vector
        # ===================================================================

        sa.Column(
            "feature_vector",
            sa.JSON(),
            nullable=False,
        ),

        # ===================================================================
        # Timestamps
        # ===================================================================

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),

        sa.PrimaryKeyConstraint("id"),

        # -------------------------------------------------------------------
        # Dataset Version FK
        # -------------------------------------------------------------------

        sa.ForeignKeyConstraint(
            ["dataset_version_id"],
            ["dataset_versions.id"],
            name="fk_dataset_samples_dataset_version_id",
            ondelete="CASCADE",
        ),

        # -------------------------------------------------------------------
        # Module 02 Email FK
        # -------------------------------------------------------------------

        sa.ForeignKeyConstraint(
            ["email_id"],
            ["emails.id"],
            name="fk_dataset_samples_email_id",
            ondelete="RESTRICT",
        ),

        # -------------------------------------------------------------------
        # Module 04 Feature FK
        # -------------------------------------------------------------------

        sa.ForeignKeyConstraint(
            ["feature_record_id"],
            ["email_features.id"],
            name="fk_dataset_samples_feature_record_id",
            ondelete="SET NULL",
        ),

        # -------------------------------------------------------------------
        # One email can appear only once in a dataset version
        # -------------------------------------------------------------------

        sa.UniqueConstraint(
            "dataset_version_id",
            "email_id",
            name="uq_dataset_version_email",
        ),
    )

    # =======================================================================
    # 4. dataset_samples indexes
    # =======================================================================

    op.create_index(
        "ix_dataset_samples_dataset_version_id",
        "dataset_samples",
        ["dataset_version_id"],
        unique=False,
    )

    op.create_index(
        "ix_dataset_samples_email_id",
        "dataset_samples",
        ["email_id"],
        unique=False,
    )

    op.create_index(
        "ix_dataset_samples_feature_record_id",
        "dataset_samples",
        ["feature_record_id"],
        unique=False,
    )

    op.create_index(
        "ix_dataset_samples_label",
        "dataset_samples",
        ["label"],
        unique=False,
    )

    op.create_index(
        "ix_dataset_samples_validation_status",
        "dataset_samples",
        ["validation_status"],
        unique=False,
    )

    op.create_index(
        "ix_dataset_samples_duplicate_group_id",
        "dataset_samples",
        ["duplicate_group_id"],
        unique=False,
    )

    op.create_index(
        "ix_dataset_samples_split",
        "dataset_samples",
        ["split"],
        unique=False,
    )

    op.create_index(
        "ix_dataset_samples_version_label",
        "dataset_samples",
        ["dataset_version_id", "label"],
        unique=False,
    )

    op.create_index(
        "ix_dataset_samples_version_validation",
        "dataset_samples",
        ["dataset_version_id", "validation_status"],
        unique=False,
    )

    op.create_index(
        "ix_dataset_samples_version_split",
        "dataset_samples",
        ["dataset_version_id", "split"],
        unique=False,
    )


# ---------------------------------------------------------------------------
# Downgrade
# ---------------------------------------------------------------------------


def downgrade() -> None:
    """
    Remove Dataset Management tables.

    Tables are removed in dependency order.
    """

    # =======================================================================
    # 1. dataset_samples indexes
    # =======================================================================

    op.drop_index(
        "ix_dataset_samples_version_split",
        table_name="dataset_samples",
    )

    op.drop_index(
        "ix_dataset_samples_version_validation",
        table_name="dataset_samples",
    )

    op.drop_index(
        "ix_dataset_samples_version_label",
        table_name="dataset_samples",
    )

    op.drop_index(
        "ix_dataset_samples_split",
        table_name="dataset_samples",
    )

    op.drop_index(
        "ix_dataset_samples_duplicate_group_id",
        table_name="dataset_samples",
    )

    op.drop_index(
        "ix_dataset_samples_validation_status",
        table_name="dataset_samples",
    )

    op.drop_index(
        "ix_dataset_samples_label",
        table_name="dataset_samples",
    )

    op.drop_index(
        "ix_dataset_samples_feature_record_id",
        table_name="dataset_samples",
    )

    op.drop_index(
        "ix_dataset_samples_email_id",
        table_name="dataset_samples",
    )

    op.drop_index(
        "ix_dataset_samples_dataset_version_id",
        table_name="dataset_samples",
    )

    # =======================================================================
    # 2. dataset_samples
    # =======================================================================

    op.drop_table("dataset_samples")

    # =======================================================================
    # 3. dataset_versions indexes
    # =======================================================================

    op.drop_index(
        "ix_dataset_versions_dataset_status",
        table_name="dataset_versions",
    )

    op.drop_index(
        "ix_dataset_versions_status",
        table_name="dataset_versions",
    )

    op.drop_index(
        "ix_dataset_versions_dataset_id",
        table_name="dataset_versions",
    )

    # =======================================================================
    # 4. dataset_versions
    # =======================================================================

    op.drop_table("dataset_versions")

    # =======================================================================
    # 5. datasets indexes
    # =======================================================================

    op.drop_index(
        "ix_datasets_status",
        table_name="datasets",
    )

    op.drop_index(
        "ix_datasets_name",
        table_name="datasets",
    )

    # =======================================================================
    # 6. datasets
    # =======================================================================

    op.drop_table("datasets")
