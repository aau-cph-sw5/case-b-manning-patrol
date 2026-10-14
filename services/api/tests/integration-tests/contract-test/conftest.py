from contextlib import asynccontextmanager
from uuid import UUID

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from src.db.main import get_session
from src.main import app
from src.models import PatrolArea, Station
from src.models.patrol_area import AreaKind

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
