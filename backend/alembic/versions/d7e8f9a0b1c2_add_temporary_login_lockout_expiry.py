"""Add an expiry for automatic failed-login lockouts.

Revision ID: d7e8f9a0b1c2
Revises: c8271b6a90de
Create Date: 2026-10-21
"""

from datetime import datetime, timedelta, timezone
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d7e8f9a0b1c2"
down_revision: Union[str, Sequence[str], None] = "c8271b6a90de"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("lockout_expires_at", sa.DateTime(timezone=True), nullable=True),
    )

    users = sa.table(
        "users",
        sa.column("id", sa.String(length=36)),
        sa.column("is_locked", sa.Boolean()),
        sa.column("failed_login_attempts", sa.Integer()),
        sa.column("locked_at", sa.DateTime(timezone=True)),
        sa.column("lockout_expires_at", sa.DateTime(timezone=True)),
    )
    connection = op.get_bind()
    rows = connection.execute(
        sa.select(users.c.id, users.c.locked_at).where(
            users.c.is_locked.is_(True),
            users.c.failed_login_attempts >= 5,
            users.c.locked_at.is_not(None),
        )
    ).all()
    for row in rows:
        locked_at = row.locked_at
        if isinstance(locked_at, str):
            locked_at = datetime.fromisoformat(locked_at)
        if locked_at.tzinfo is None:
            locked_at = locked_at.replace(tzinfo=timezone.utc)
        connection.execute(
            users.update()
            .where(users.c.id == row.id)
            .values(lockout_expires_at=locked_at + timedelta(minutes=15))
        )


def downgrade() -> None:
    op.drop_column("users", "lockout_expires_at")
