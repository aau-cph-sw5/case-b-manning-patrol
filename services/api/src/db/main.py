"""Database engine and schema setup."""

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel import SQLModel

from src.db import models  # noqa: F401  registers table metadata

from .system_config import system_config

ALEMBIC_INI = Path(__file__).resolve().parents[2] / "alembic.ini"

engine: AsyncEngine = create_async_engine(
    system_config.DATABASE_URL.get_secret_value(), echo=False
)


def upgrade_db() -> None:
    """Apply all pending Alembic migrations to the configured database."""
    command.upgrade(Config(ALEMBIC_INI), "head")


async def init_db(engine_: AsyncEngine | None = None) -> None:
    """Create missing tables from the SQLModel metadata.

    Uses the app engine unless ``engine_`` is given. Existing tables are not
    altered; schema changes go through Alembic migrations.
    """
    async with (engine_ or engine).begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
