"""add adjustment author table

Revision ID: bd3f2068fdcd
Revises: c4b969647080
Create Date: 2026-11-14 10:20:29.379262

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "bd3f2068fdcd"
down_revision: str | Sequence[str] | None = "c4b969647080"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade():
    op.create_table(
        "adjustment_author",
        sa.Column("adjustment_id", sa.Uuid(), nullable=False),
        sa.Column("android_id", sa.Uuid(), nullable=True),
        sa.Column("reason", sa.String(), nullable=True),
        sa.Column("author", sa.String(), nullable=True),
        sa.Column("server_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(), nullable=False, server_default="api"),
        sa.Column("anonymized_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("adjustment_id"),
        sa.ForeignKeyConstraint(["adjustment_id"], ["adjustment.adjustment_id"]),
    )


def downgrade():
    op.drop_table("adjustment_author")
