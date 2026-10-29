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
    command.upgrade(Config(ALEMBIC_INI), "head")


async def init_db(engine_: AsyncEngine | None = None) -> None:
    async with (engine_ or engine).begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
