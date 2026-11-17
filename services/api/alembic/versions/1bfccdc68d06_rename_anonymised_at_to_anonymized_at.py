"""rename anonymised_at to anonymized_at

Revision ID: 1bfccdc68d06
Revises: 93899d02d7fb
Create Date: 2026-11-16 13:12:59.925157

Spells the column like adjustment_author.anonymized_at, so both anonymized
tables use the same name. Renamed in place, so existing values are kept.
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1bfccdc68d06"
down_revision: str | Sequence[str] | None = "93899d02d7fb"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Rename steward_shift_identity.anonymised_at to anonymized_at."""
    with op.batch_alter_table("steward_shift_identity") as batch_op:
        batch_op.alter_column("anonymised_at", new_column_name="anonymized_at")


def downgrade() -> None:
    """Rename steward_shift_identity.anonymized_at back to anonymised_at."""
    with op.batch_alter_table("steward_shift_identity") as batch_op:
        batch_op.alter_column("anonymized_at", new_column_name="anonymised_at")
