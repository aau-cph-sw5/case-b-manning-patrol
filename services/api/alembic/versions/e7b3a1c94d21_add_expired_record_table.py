"""add expired record table

Revision ID: e7b3a1c94d21
Revises: 170fefe814f7
Create Date: 2026-11-17 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e7b3a1c94d21"
down_revision: str | Sequence[str] | None = "170fefe814f7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "expiredrecord",
        sa.Column("expired_id", sa.Uuid(), nullable=False),
        sa.Column(
            "target",
            sa.Enum(
                "STEWARD_SHIFT_IDENTITY",
                "ADJUSTMENT_AUTHOR",
                name="expiredtarget",
            ),
            nullable=False,
        ),
        sa.Column("record_id", sa.Uuid(), nullable=False),
        sa.Column("server_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(), nullable=False, server_default="anonymizer"),
        sa.PrimaryKeyConstraint("expired_id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("expiredrecord")
