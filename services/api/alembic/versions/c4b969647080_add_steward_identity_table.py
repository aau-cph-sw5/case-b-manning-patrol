"""add steward identity table

Revision ID: c4b969647080
Revises: a004a99997d0
Create Date: 2026-11-12 10:59:20.073752

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c4b969647080"
down_revision: str | Sequence[str] | None = "a004a99997d0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "steward_shift_identity",
        sa.Column("steward_ref", sa.Uuid(), nullable=False),
        sa.Column("android_id", sa.Uuid(), nullable=True),
        sa.Column("shift_start", sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.Column("anonymised_at", sqlmodel.sql.sqltypes.UTCDateTime(), nullable=True),
        sa.PrimaryKeyConstraint("steward_ref"),
        sa.UniqueConstraint("android_id", "shift_start"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("steward_shift_identity")
