import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite://")

from collections.abc import AsyncGenerator, Generator  # noqa: E402

import pytest  # noqa: E402
from sqlalchemy.ext.asyncio import create_async_engine  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402
from sqlmodel import SQLModel  # noqa: E402
from sqlmodel.ext.asyncio.session import AsyncSession  # noqa: E402

from src.db.main import get_session  # noqa: E402
from src.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def override_db_session() -> Generator[None]:
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    tables_created = False

    async def get_test_session() -> AsyncGenerator[AsyncSession]:
        nonlocal tables_created
        if not tables_created:
            async with engine.begin() as conn:
                await conn.run_sync(SQLModel.metadata.create_all)
            tables_created = True
        async with AsyncSession(engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_test_session
    yield
    app.dependency_overrides.pop(get_session, None)
