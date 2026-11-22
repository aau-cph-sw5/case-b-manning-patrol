"""merge expired record and steward merge heads

Revision ID: 6594c8483332
Revises: 546c62b7ad7b, e7b3a1c94d21
Create Date: 2026-11-22 08:51:54.545329

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "6594c8483332"
down_revision: str | Sequence[str] | None = ("546c62b7ad7b", "e7b3a1c94d21")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
