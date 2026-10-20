import os
from collections.abc import AsyncGenerator, Generator  # noqa: E402
from contextlib import asynccontextmanager
from uuid import UUID

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402
from sqlmodel import SQLModel  # noqa: E402
from sqlmodel.ext.asyncio.session import AsyncSession  # noqa: E402

from src.db.main import get_session
from src.main import app
from src.models import PatrolArea, Station
from src.models.patrol_area import AreaKind

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite://")


class _StubCoverageUpdater:
    """Stands in for CoverageUpdater: the coverage pipeline is a skeleton
    (compute/track raise NotImplementedError), so a real refresh would fail.
    Tests only need the attribute to exist on app.state."""

    async def refresh(self) -> None:
        return None


app.state.coverage_updater = _StubCoverageUpdater()

SEEDED_STATION_ID = "STN-001"
SEEDED_BEACON_ID = "550e8400-e29b-41d4-a716-446655440000"


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest_asyncio.fixture
async def seeded_station_id() -> str:
    get_test_session = app.dependency_overrides[get_session]
    async with asynccontextmanager(get_test_session)() as session:
        session.add(Station(id=SEEDED_STATION_ID, name="Station 01"))
        session.add(
            PatrolArea(
                beacon_id=UUID(SEEDED_BEACON_ID),
                station_id=SEEDED_STATION_ID,
                area_id="PA-001-P",
                area_kind=AreaKind.PLATFORM,
            )
        )
        await session.commit()
    return SEEDED_STATION_ID


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
