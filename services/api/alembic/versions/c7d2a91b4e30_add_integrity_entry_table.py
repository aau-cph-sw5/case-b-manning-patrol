"""add integrity entry table

Revision ID: c7d2a91b4e30
Revises: a004a99997d0
Create Date: 2026-11-11 14:12:30.418291

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c7d2a91b4e30"
down_revision: str | Sequence[str] | None = "a004a99997d0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "integrityentry",
        sa.Column("entry_id", sa.Uuid(), nullable=False),
        sa.Column("chain", sa.String(length=32), nullable=False),
        sa.Column("seq", sa.Integer(), nullable=False),
        sa.Column("record_type", sa.String(length=32), nullable=False),
        sa.Column("record_id", sa.Uuid(), nullable=False),
        sa.Column("prev_hash", sa.String(length=64), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("head_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "server_timestamp",
            sqlmodel.sql.sqltypes.UTCDateTime(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("entry_id"),
        sa.UniqueConstraint("chain", "seq"),
    )
    op.create_index(
        op.f("ix_integrityentry_chain"), "integrityentry", ["chain"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_integrityentry_chain"), table_name="integrityentry")
    op.drop_table("integrityentry")
