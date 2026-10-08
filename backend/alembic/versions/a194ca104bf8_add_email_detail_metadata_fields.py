"""add email detail metadata fields

Revision ID: a194ca104bf8
Revises: 5fe8dbb2a2fb
Create Date: 2026-09-25 20:42:48.843953

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# ============================================================================
# Revision identifiers
# ============================================================================

revision: str = "a194ca104bf8"
down_revision: Union[str, Sequence[str], None] = "5fe8dbb2a2fb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ============================================================================
# Upgrade
# ============================================================================

def upgrade() -> None:
    """
    Add additional email metadata fields required by the
    Email Details view.

    New fields:
        - cc
        - bcc
        - reply_to
        - content_type
        - mime_version

    All fields are nullable because existing email records may
    not contain these headers.
    """

    op.add_column(
        "emails",
        sa.Column(
            "cc",
            sa.Text(),
            nullable=True,
        ),
    )

    op.add_column(
        "emails",
        sa.Column(
            "bcc",
            sa.Text(),
            nullable=True,
        ),
    )

    op.add_column(
        "emails",
        sa.Column(
            "reply_to",
            sa.String(length=512),
            nullable=True,
        ),
    )

    op.add_column(
        "emails",
        sa.Column(
            "content_type",
            sa.String(length=255),
            nullable=True,
        ),
    )

    op.add_column(
        "emails",
        sa.Column(
            "mime_version",
            sa.String(length=64),
            nullable=True,
        ),
    )


# ============================================================================
# Downgrade
# ============================================================================

def downgrade() -> None:
    """
    Remove the additional email metadata fields.
    """

    op.drop_column(
        "emails",
        "mime_version",
    )

    op.drop_column(
        "emails",
        "content_type",
    )

    op.drop_column(
        "emails",
        "reply_to",
    )

    op.drop_column(
        "emails",
        "bcc",
    )

    op.drop_column(
        "emails",
        "cc",
    )
