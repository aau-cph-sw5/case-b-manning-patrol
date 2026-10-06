from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models import patrol_area, station  # noqa: F401  registers table metadata

from .config import settings

engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL.get_secret_value(), echo=False
)


async def get_session() -> AsyncGenerator[AsyncSession]:
    async with AsyncSession(engine) as session:
        yield session


async def init_db(engine_: AsyncEngine | None = None) -> None:
    async with (engine_ or engine).begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
