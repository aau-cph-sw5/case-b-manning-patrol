"""add config table

Revision ID: a004a99997d0
Revises: 5c1a7e3d9b42
Create Date: 2026-10-23 13:09:48.077225

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a004a99997d0"
down_revision: str | Sequence[str] | None = "5c1a7e3d9b42"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "config",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("at_risk_threshold_minutes", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    config = sa.table(
        "config",
        sa.Column("id", sa.Integer()),
        sa.Column("at_risk_threshold_minutes", sa.Integer()),
    )
    op.bulk_insert(config, [{"id": 1, "at_risk_threshold_minutes": 10}])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("config")
