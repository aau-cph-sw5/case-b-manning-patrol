from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

import src.models  # noqa: F401  registrerer tabel-metadata


@pytest.fixture
async def engine() -> AsyncGenerator[AsyncEngine]:
    engine = create_async_engine("sqlite+aiosqlite://")
    yield engine
    await engine.dispose()


@pytest.fixture
async def session_factory(engine):
    async def factory():
        async with AsyncSession(engine) as session:
            yield session

    return factory


@pytest.fixture
def app():
    from src.main import app

    return app
