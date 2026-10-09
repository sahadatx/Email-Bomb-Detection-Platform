"""Align experiment actor ID with the platform's string UUID user IDs.

Revision ID: a8b9c0d1e2f3
Revises: f7a8b9c0d1e2
"""
from alembic import op
import sqlalchemy as sa

revision = "a8b9c0d1e2f3"
down_revision = "f7a8b9c0d1e2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The first Experiments migration used native UUID while User.id is
    # String(36). Batch mode rebuilds safely on SQLite and alters in place on
    # databases that support ALTER COLUMN.
    if op.get_bind().dialect.name == "sqlite":
        with op.batch_alter_table("experiments", recreate="always") as batch:
            batch.alter_column(
                "created_by_id",
                existing_type=sa.Uuid(),
                type_=sa.String(length=36),
                existing_nullable=True,
            )
    else:
        op.alter_column(
            "experiments",
            "created_by_id",
            existing_type=sa.Uuid(),
            type_=sa.String(length=36),
            existing_nullable=True,
            postgresql_using="created_by_id::text",
        )


def downgrade() -> None:
    if op.get_bind().dialect.name == "sqlite":
        with op.batch_alter_table("experiments", recreate="always") as batch:
            batch.alter_column(
                "created_by_id",
                existing_type=sa.String(length=36),
                type_=sa.Uuid(),
                existing_nullable=True,
            )
    else:
        op.alter_column(
            "experiments",
            "created_by_id",
            existing_type=sa.String(length=36),
            type_=sa.Uuid(),
            existing_nullable=True,
            postgresql_using="created_by_id::uuid",
        )
