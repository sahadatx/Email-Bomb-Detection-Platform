"""add configurable default active model version for detection

Revision ID: f4c5d6e7a8b9
Revises: f2b3c4d5e6f7
Create Date: 2026-09-30
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f4c5d6e7a8b9"
down_revision: Union[str, Sequence[str], None] = "f2b3c4d5e6f7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("detection_settings") as batch_op:
        batch_op.add_column(
            sa.Column("default_model_version_id", sa.Uuid(), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_detection_settings_default_model_version",
            "ml_model_versions",
            ["default_model_version_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    with op.batch_alter_table("detection_settings") as batch_op:
        batch_op.drop_constraint(
            "fk_detection_settings_default_model_version", type_="foreignkey"
        )
        batch_op.drop_column("default_model_version_id")
