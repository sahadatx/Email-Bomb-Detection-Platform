"""add email ground truth label

Revision ID: 5fe8dbb2a2fb
Revises: 0f587db84483
Create Date: 2026-09-25
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# ============================================================
# REVISION IDENTIFIERS
# ============================================================

revision: str = "5fe8dbb2a2fb"
down_revision: str | Sequence[str] | None = "0f587db84483"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# ============================================================
# UPGRADE
# ============================================================


def upgrade() -> None:
    """
    Add the required ground-truth label column to emails.

    Existing email records have already been intentionally removed
    as part of the controlled Module 02 reset, so the new column can
    be created as NOT NULL without a temporary default value.

    Valid values:
        normal
        bombing
    """

    op.add_column(
        "emails",
        sa.Column(
            "ground_truth_label",
            sa.String(length=20),
            nullable=False,
        ),
    )

    op.create_index(
        "ix_emails_ground_truth_label",
        "emails",
        ["ground_truth_label"],
        unique=False,
    )


# ============================================================
# DOWNGRADE
# ============================================================


def downgrade() -> None:
    """
    Remove the ground-truth label column and its index.
    """

    op.drop_index(
        "ix_emails_ground_truth_label",
        table_name="emails",
    )

    op.drop_column(
        "emails",
        "ground_truth_label",
    )
