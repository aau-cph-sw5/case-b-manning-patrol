import json
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.ingest import load_stations
from src.models import PatrolArea, Station

# Mock data shaped exactly like services/api/src/data/stations.v1.json.
STATION = {
    "id": "STN-001",
    "name": "Station 01",
    "line_ids": ["M1"],
    "patrol_areas": [
        {
            "id": "PA-001-P",
            "kind": "platform",
            "beacon_id": "660e8400-e29b-41d4-a716-446655440001",
        },
        {
            "id": "PA-001-C",
            "kind": "concourse",
            "beacon_id": "660e8400-e29b-41d4-a716-446655440081",
        },
    ],
}

# A second station used to simulate "someone edited the data file"
EXTRA_STATION = {
    "id": "STN-002",
    "name": "Station 02",
    "line_ids": ["M1"],
    "patrol_areas": [
        {
            "id": "PA-002-P",
            "kind": "platform",
            "beacon_id": "660e8400-e29b-41d4-a716-446655440002",
        },
    ],
}


def write_stations_file(path: Path, stations: list[dict]) -> Path:
    """Write the given station entries to a JSON file, like stations.v1.json."""

    path.write_text(json.dumps({"stations": stations}), encoding="utf-8")
    return path


@pytest_asyncio.fixture
async def session():
    """Give every test a fresh database session.

    Instead of talking to the real Postgres database, each test gets an
    in-memory SQLite database ("sqlite+aiosqlite://"). The tests therefore
    run anywhere without setup, and never touch real data.

    StaticPool keeps a single shared connection, so the whole test sees the
    same in-memory database instead of a new empty one per connection.
    """
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)

    # Create every SQLModel table (station, patrol_area, ...) in the
    # in-memory database.
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    # yield = the test runs here with this session; afterwards the
    # engine is shut down and the in-memory database is discarded.
    async with AsyncSession(engine) as session:
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_load_stations_loads_station_and_patrol_areas(session, tmp_path):
    """Ingesting a data file puts its stations and patrol areas in the DB.

    tmp_path is a pytest fixture: a unique temporary directory that is
    automatically cleaned up after the test.
    """
    path = write_stations_file(tmp_path / "stations.json", [STATION])

    await load_stations(session, path)

    # The station row must exist with the values from the JSON entry.
    stations = (await session.exec(select(Station))).all()
    assert [station.id for station in stations] == ["STN-001"]
    assert stations[0].name == "Station 01"
    assert stations[0].line_ids == ["M1"]

    # Both of the station's patrol areas must have been ingested too.
    areas = (await session.exec(select(PatrolArea))).all()
    assert {area.id for area in areas} == {"PA-001-P", "PA-001-C"}


@pytest.mark.asyncio
async def test_station_added_to_file_appears_without_code_change(session, tmp_path):
    """A station added to the data file appears after re-ingest."""

    path = write_stations_file(tmp_path / "stations.json", [STATION])
    await load_stations(session, path)

    write_stations_file(path, [STATION, EXTRA_STATION])
    await load_stations(session, path)

    # Both stations must now be in the database.
    stations = (await session.exec(select(Station))).all()
    assert [station.id for station in stations] == ["STN-001", "STN-002"]

    # The new station's patrol areas must be ingested along with it.
    areas = (await session.exec(select(PatrolArea))).all()
    assert {area.id for area in areas} == {"PA-001-P", "PA-001-C", "PA-002-P"}
