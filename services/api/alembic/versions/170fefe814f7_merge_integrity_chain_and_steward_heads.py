"""merge integrity chain and steward heads

Revision ID: 170fefe814f7
Revises: 1bfccdc68d06, c7d2a91b4e30
Create Date: 2026-11-16 13:51:25.127544

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "170fefe814f7"
down_revision: str | Sequence[str] | None = ("1bfccdc68d06", "c7d2a91b4e30")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
