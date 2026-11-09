"""add overdue log

Revision ID: 2d643ec8f6f5
Revises: 2270e5bed9b6
Create Date: 2026-10-22 10:30:51.998498

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2d643ec8f6f5"
down_revision: str | Sequence[str] | None = "2270e5bed9b6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "overdue_log",
        sa.Column("entry_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("entry_type", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("station_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("area_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("area_kind", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("overdue_at", sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.Column("detected_at", sqlmodel.sql.sqltypes.UTCDateTime(), nullable=True),
        sa.Column(
            "last_covered_at", sqlmodel.sql.sqltypes.UTCDateTime(), nullable=True
        ),
        sa.Column("cleared_at", sqlmodel.sql.sqltypes.UTCDateTime(), nullable=True),
        sa.Column("source", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.PrimaryKeyConstraint("entry_id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("overdue_log")
