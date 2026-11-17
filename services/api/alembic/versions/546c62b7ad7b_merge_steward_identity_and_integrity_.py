"""merge steward identity and integrity chain migrations

Revision ID: 546c62b7ad7b
Revises: c4b969647080, c7d2a91b4e30
Create Date: 2026-11-17 13:06:41.990616

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "546c62b7ad7b"
down_revision: str | Sequence[str] | None = ("c4b969647080", "c7d2a91b4e30")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
