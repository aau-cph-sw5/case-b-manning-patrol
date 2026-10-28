from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Annotated

from alembic import command
from alembic.config import Config
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db import models  # noqa: F401  registers table metadata

from .system_config import system_config

ALEMBIC_INI = Path(__file__).resolve().parents[2] / "alembic.ini"

engine: AsyncEngine = create_async_engine(
    system_config.DATABASE_URL.get_secret_value(), echo=False
)


def upgrade_db() -> None:
    """Apply all Alembic migrations. Call outside a running event loop."""
    command.upgrade(Config(ALEMBIC_INI), "head")


async def get_session() -> AsyncGenerator[AsyncSession]:
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def init_db(engine_: AsyncEngine | None = None) -> None:
    async with (engine_ or engine).begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
