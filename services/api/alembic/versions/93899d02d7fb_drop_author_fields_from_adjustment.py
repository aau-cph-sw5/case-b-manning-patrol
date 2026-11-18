"""drop author fields from adjustment

Revision ID: 93899d02d7fb
Revises: ecdd46b8a7ae
Create Date: 2026-11-16 12:54:42.849845

The author fields moved to adjustment_author so they can be anonymized
without touching the append-only adjustment table. Existing values are not
copied over, since databases only hold test data.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "93899d02d7fb"
down_revision: str | Sequence[str] | None = "ecdd46b8a7ae"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Drop android_id, reason and author from adjustment."""
    with op.batch_alter_table("adjustment") as batch_op:
        batch_op.drop_column("android_id")
        batch_op.drop_column("reason")
        batch_op.drop_column("author")


def downgrade() -> None:
    """Re-add the author fields as nullable; their values are not restored."""
    with op.batch_alter_table("adjustment") as batch_op:
        batch_op.add_column(sa.Column("android_id", sa.Uuid(), nullable=True))
        batch_op.add_column(sa.Column("reason", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("author", sa.String(), nullable=True))
