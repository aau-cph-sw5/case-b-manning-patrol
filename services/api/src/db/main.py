from collections.abc import AsyncGenerator
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models import (  # noqa: F401  registers table metadata
    event,
    overdue_log,
    patrol_area,
    station,
)

from .config import settings

ALEMBIC_INI = Path(__file__).resolve().parents[2] / "alembic.ini"

engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL.get_secret_value(), echo=False
)


def upgrade_db() -> None:
    """Apply all Alembic migrations. Call outside a running event loop."""
    command.upgrade(Config(ALEMBIC_INI), "head")


async def get_session() -> AsyncGenerator[AsyncSession]:
    async with AsyncSession(engine) as session:
        yield session


async def init_db(engine_: AsyncEngine | None = None) -> None:
    async with (engine_ or engine).begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
