"""rename actor and beacon to uuid ids

Revision ID: 5c1a7e3d9b42
Revises: 2d643ec8f6f5
Create Date: 2026-10-22 14:00:00.000000

Renames event.actor -> android_id, event.beacon -> beacon_id and
adjustment.actor -> android_id, and changes them and
adjustment.corrected_beacon_id from strings to UUIDs. Renamed in place, so
existing rows are kept. On PostgreSQL the type change casts each value, so the
upgrade fails if a row holds a value that is not a UUID (for example the old
placeholder "Actor1"); reset such a database with `uv run reset-db`.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5c1a7e3d9b42"
down_revision: str | Sequence[str] | None = "2d643ec8f6f5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _to_uuid(
    batch_op,
    column: str,
    nullable: bool,
) -> None:
    batch_op.alter_column(
        column,
        existing_type=sa.VARCHAR(),
        type_=sa.Uuid(),
        existing_nullable=nullable,
        postgresql_using=f"{column}::uuid",
    )


def _to_varchar(
    batch_op,
    column: str,
    nullable: bool,
) -> None:
    batch_op.alter_column(
        column,
        existing_type=sa.Uuid(),
        type_=sa.VARCHAR(),
        existing_nullable=nullable,
        postgresql_using=f"{column}::text",
    )


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("event") as batch_op:
        batch_op.alter_column(
            "actor",
            new_column_name="android_id",
            existing_type=sa.VARCHAR(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "beacon",
            new_column_name="beacon_id",
            existing_type=sa.VARCHAR(),
            existing_nullable=True,
        )
    with op.batch_alter_table("event") as batch_op:
        _to_uuid(batch_op, "android_id", nullable=False)
        _to_uuid(batch_op, "beacon_id", nullable=True)

    with op.batch_alter_table("adjustment") as batch_op:
        batch_op.alter_column(
            "actor",
            new_column_name="android_id",
            existing_type=sa.VARCHAR(),
            existing_nullable=False,
        )
    with op.batch_alter_table("adjustment") as batch_op:
        _to_uuid(batch_op, "android_id", nullable=False)
        _to_uuid(batch_op, "corrected_beacon_id", nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("adjustment") as batch_op:
        _to_varchar(batch_op, "android_id", nullable=False)
        _to_varchar(batch_op, "corrected_beacon_id", nullable=True)
    with op.batch_alter_table("adjustment") as batch_op:
        batch_op.alter_column(
            "android_id",
            new_column_name="actor",
            existing_type=sa.VARCHAR(),
            existing_nullable=False,
        )

    with op.batch_alter_table("event") as batch_op:
        _to_varchar(batch_op, "android_id", nullable=False)
        _to_varchar(batch_op, "beacon_id", nullable=True)
    with op.batch_alter_table("event") as batch_op:
        batch_op.alter_column(
            "android_id",
            new_column_name="actor",
            existing_type=sa.VARCHAR(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "beacon_id",
            new_column_name="beacon",
            existing_type=sa.VARCHAR(),
            existing_nullable=True,
        )
