"""drop android_id from event

Revision ID: ecdd46b8a7ae
Revises: 9a981ed74ca0
Create Date: 2026-11-16 12:45:26.858915

Events now reference the steward only through steward_ref, so the device ID
lives in steward_shift_identity alone and can be anonymized there. Existing
events have no steward_ref and are deleted, since databases only hold test
data; reseed with `uv run reset-db`.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ecdd46b8a7ae"
down_revision: str | Sequence[str] | None = "9a981ed74ca0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Delete events without steward_ref, make it required, drop android_id."""
    op.execute("DELETE FROM event WHERE steward_ref IS NULL")
    with op.batch_alter_table("event") as batch_op:
        batch_op.alter_column("steward_ref", existing_type=sa.Uuid(), nullable=False)
        batch_op.drop_column("android_id")


def downgrade() -> None:
    """Re-add android_id as nullable; deleted events are not restored."""
    with op.batch_alter_table("event") as batch_op:
        batch_op.add_column(sa.Column("android_id", sa.Uuid(), nullable=True))
        batch_op.alter_column("steward_ref", existing_type=sa.Uuid(), nullable=True)
