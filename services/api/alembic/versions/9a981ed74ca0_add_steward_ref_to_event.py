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
    with op.batch_alter_table("event") as batch_op:
        batch_op.add_column(sa.Column("steward_ref", sa.Uuid(), nullable=True))
        batch_op.create_foreign_key(
            "event_steward_ref_fkey",
            "steward_shift_identity",
            ["steward_ref"],
            ["steward_ref"],
        )


def downgrade():
    with op.batch_alter_table("event") as batch_op:
        batch_op.drop_constraint("event_steward_ref_fkey", type_="foreignkey")
        batch_op.drop_column("steward_ref")
