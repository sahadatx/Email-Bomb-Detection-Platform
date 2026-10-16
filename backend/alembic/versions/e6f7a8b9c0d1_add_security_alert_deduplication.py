"""add rule scoped security alert grouping key"""

from alembic import op
import sqlalchemy as sa

revision = "e6f7a8b9c0d1"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("security_alerts", sa.Column("deduplication_key", sa.String(length=64), nullable=True))
    op.create_index("ix_security_alerts_deduplication_key", "security_alerts", ["deduplication_key"])


def downgrade() -> None:
    op.drop_index("ix_security_alerts_deduplication_key", table_name="security_alerts")
    op.drop_column("security_alerts", "deduplication_key")
