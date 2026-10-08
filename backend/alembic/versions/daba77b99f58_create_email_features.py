"""create email features

Revision ID: daba77b99f58
Revises: ea9f98c8a603
Create Date: 2026-09-25 12:03:25.721082

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# ============================================================
# REVISION IDENTIFIERS
# ============================================================

revision: str = "daba77b99f58"
down_revision: Union[str, Sequence[str], None] = "ea9f98c8a603"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ============================================================
# UPGRADE
# ============================================================

def upgrade() -> None:
    """Create the email_features table and its indexes."""

    op.create_table(
        "email_features",

        # ----------------------------------------------------
        # Primary identity
        # ----------------------------------------------------

        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
        ),

        sa.Column(
            "email_id",
            sa.Uuid(),
            nullable=False,
        ),

        # ----------------------------------------------------
        # F1-F12
        # ----------------------------------------------------

        # F1 — Sender Email
        sa.Column(
            "f1_sender_email",
            sa.String(length=512),
            nullable=True,
        ),

        # F2 — Known Domain Indicator
        sa.Column(
            "f2_known_domain",
            sa.Boolean(),
            nullable=False,
        ),

        # F3 — Message-ID Presence
        sa.Column(
            "f3_message_id",
            sa.Boolean(),
            nullable=False,
        ),

        # F4 — Auto-Submitted Header
        sa.Column(
            "f4_auto_submitted",
            sa.Boolean(),
            nullable=False,
        ),

        # F5 — Precedence Bulk Indicator
        sa.Column(
            "f5_precedence_bulk",
            sa.Boolean(),
            nullable=False,
        ),

        # F6 — List-Id Header
        sa.Column(
            "f6_list_id",
            sa.Boolean(),
            nullable=False,
        ),

        # F7 — X-BeenThere Header
        sa.Column(
            "f7_x_beenthere",
            sa.Boolean(),
            nullable=False,
        ),

        # F8 — X-Anti-Abuse Header
        sa.Column(
            "f8_x_anti_abuse",
            sa.Boolean(),
            nullable=False,
        ),

        # F9 — Keyword-Based Content Features
        sa.Column(
            "f9_keyword_features",
            sa.Integer(),
            nullable=False,
        ),

        # F10 — Subject Length
        sa.Column(
            "f10_subject_length",
            sa.Integer(),
            nullable=False,
        ),

        # F11 — Emails Per Minute
        sa.Column(
            "f11_emails_per_minute",
            sa.Integer(),
            nullable=False,
        ),

        # F12 — Emails Per Hour
        sa.Column(
            "f12_emails_per_hour",
            sa.Integer(),
            nullable=False,
        ),

        # ----------------------------------------------------
        # Complete feature vector
        # ----------------------------------------------------

        sa.Column(
            "feature_vector",
            sa.JSON(),
            nullable=False,
        ),

        # ----------------------------------------------------
        # Validation
        # ----------------------------------------------------

        sa.Column(
            "validation_errors",
            sa.JSON(),
            nullable=False,
        ),

        sa.Column(
            "validation_warnings",
            sa.JSON(),
            nullable=False,
        ),

        # ----------------------------------------------------
        # Extraction status
        # ----------------------------------------------------

        sa.Column(
            "status",
            sa.Enum(
                "extracted",
                "warning",
                "failed",
                name="feature_extraction_status",
                native_enum=False,
            ),
            nullable=False,
        ),

        # ----------------------------------------------------
        # Extraction metadata
        # ----------------------------------------------------

        sa.Column(
            "extractor_version",
            sa.String(length=32),
            nullable=False,
        ),

        sa.Column(
            "processing_time_ms",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "extracted_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),

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

        # ----------------------------------------------------
        # Relationships
        # ----------------------------------------------------

        sa.ForeignKeyConstraint(
            ["email_id"],
            ["emails.id"],
            ondelete="CASCADE",
        ),

        # ----------------------------------------------------
        # Primary key
        # ----------------------------------------------------

        sa.PrimaryKeyConstraint("id"),
    )

    # ========================================================
    # INDEXES
    # ========================================================

    # One feature record per email.
    #
    # This UNIQUE index guarantees that re-extraction updates
    # the existing feature record instead of creating duplicate
    # records for the same email.
    op.create_index(
        "ix_email_features_email_id",
        "email_features",
        ["email_id"],
        unique=True,
    )

    # Used for filtering/querying extraction status.
    op.create_index(
        "ix_email_features_status",
        "email_features",
        ["status"],
        unique=False,
    )


# ============================================================
# DOWNGRADE
# ============================================================

def downgrade() -> None:
    """Remove the email_features table and its indexes."""

    op.drop_index(
        "ix_email_features_status",
        table_name="email_features",
    )

    op.drop_index(
        "ix_email_features_email_id",
        table_name="email_features",
    )

    op.drop_table("email_features")
