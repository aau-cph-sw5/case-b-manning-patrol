"""add steward_ref to event

Revision ID: 9a981ed74ca0
Revises: bd3f2068fdcd
Create Date: 2026-11-14 10:30:14.611911

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9a981ed74ca0"
down_revision: str | Sequence[str] | None = "bd3f2068fdcd"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade():
    op.add_column("event", sa.Column("steward_ref", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "event_steward_ref_fkey",
        "event",
        "steward_shift_identity",
        ["steward_ref"],
        ["steward_ref"],
    )


def downgrade():
    op.drop_constraint("event_steward_ref_fkey", "event", type_="foreignkey")
    op.drop_column("event", "steward_ref")
