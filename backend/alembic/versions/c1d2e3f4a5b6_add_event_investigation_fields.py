"""add event investigation fields"""
from alembic import op
import sqlalchemy as sa

revision = "c1d2e3f4a5b6"
down_revision = "e6f7a8b9c0d1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # SQLite requires a table rebuild to add a foreign-key constraint.
    with op.batch_alter_table("security_events") as batch_op:
        batch_op.add_column(sa.Column("assigned_to", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("disposition", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("investigation_note", sa.Text(), nullable=True))
        batch_op.create_foreign_key(
            "fk_security_events_assigned_to_users",
            "users",
            ["assigned_to"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    with op.batch_alter_table("security_events") as batch_op:
        batch_op.drop_constraint("fk_security_events_assigned_to_users", type_="foreignkey")
        batch_op.drop_column("investigation_note")
        batch_op.drop_column("disposition")
        batch_op.drop_column("assigned_to")
