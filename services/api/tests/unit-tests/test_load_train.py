import json
from collections import Counter
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.ingest import (
    STATIONS_FILE,
    TRAINS_FILE,
    load_reference_data,
    load_trains,
)
from src.db.models import Line
from src.db.repository.train import get_train_lines, get_trains

# Mock data shaped exactly like services/api/src/data/trains.v1.json.
TRAIN = {
    "id": "770e8400-e29b-41d4-a716-446655440101",
    "slug": "train-1",
    "beacon_id": "660e8400-e29b-41d4-a716-446655440101",
    "line_ids": ["M1", "M2"],
}

# A second train used to simulate "someone edited the data file"
EXTRA_TRAIN = {
    "id": "770e8400-e29b-41d4-a716-446655440201",
    "slug": "train-35",
    "beacon_id": "660e8400-e29b-41d4-a716-446655440201",
    "line_ids": ["M3", "M4"],
}

LINES = [
    {"id": line_id, "name": f"Metro Line {line_id[-1]}"}
    for line_id in ("M1", "M2", "M3", "M4")
]


def write_trains_file(path: Path, trains: list[dict]) -> Path:
    """Write the given train entries to a JSON file, like trains.v1.json."""
    path.write_text(json.dumps({"trains": trains}), encoding="utf-8")
    return path


async def create_session(foreign_keys: bool):
    """Yield a session on a fresh in-memory SQLite database.

    With ``foreign_keys`` on, SQLite enforces foreign keys like Postgres does.
    StaticPool keeps one shared connection, so the whole test sees the same
    in-memory database.
    """
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)

    if foreign_keys:

        @event.listens_for(engine.sync_engine, "connect")
        def enable_foreign_keys(dbapi_connection, _):
            dbapi_connection.execute("PRAGMA foreign_keys=ON")

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSession(engine) as session:
        yield session
    await engine.dispose()


@pytest_asyncio.fixture
async def session():
    """Give every test a fresh in-memory database session."""
    async for session in create_session(foreign_keys=False):
        yield session


@pytest_asyncio.fixture
async def fk_session():
    """Give a test a fresh in-memory session that enforces foreign keys."""
    async for session in create_session(foreign_keys=True):
        yield session


@pytest.mark.asyncio
async def test_load_trains_loads_trains_and_their_lines(session, tmp_path):
    """Ingesting a data file puts its trains and train-line links in the DB."""
    session.add_all(Line(id=line["id"], name=line["name"]) for line in LINES)
    await session.commit()
    path = write_trains_file(tmp_path / "trains.json", [TRAIN])

    await load_trains(session, path)

    trains = await get_trains(session)
    assert [str(train.train_id) for train in trains] == [TRAIN["id"]]
    assert trains[0].slug == "train-1"
    assert str(trains[0].beacon_id) == TRAIN["beacon_id"]

    train_lines = await get_train_lines(session)
    assert {train_line.line_id for train_line in train_lines} == {"M1", "M2"}
    assert {str(train_line.train_id) for train_line in train_lines} == {TRAIN["id"]}


@pytest.mark.asyncio
async def test_reload_is_idempotent_and_picks_up_added_train(session, tmp_path):
    """Reloading the same file changes nothing; a train added to it appears."""
    session.add_all(Line(id=line["id"], name=line["name"]) for line in LINES)
    await session.commit()
    path = write_trains_file(tmp_path / "trains.json", [TRAIN])

    await load_trains(session, path)
    await load_trains(session, path)

    assert len(await get_trains(session)) == 1
    assert len(await get_train_lines(session)) == 2

    write_trains_file(path, [TRAIN, EXTRA_TRAIN])
    await load_trains(session, path)

    trains = await get_trains(session)
    assert {train.slug for train in trains} == {"train-1", "train-35"}
    assert len(await get_train_lines(session)) == 4


@pytest.mark.asyncio
async def test_restart_with_foreign_keys_enforced(fk_session):
    """Loading the reference data twice succeeds when foreign keys are enforced.

    The second ``load_stations`` deletes every line, which only works because
    it clears the train-line links first; ``load_trains`` then restores them.
    """
    trains = load_json(TRAINS_FILE)["trains"]
    expected_train_lines = sum(len(train["line_ids"]) for train in trains)

    await load_reference_data(fk_session)
    await load_reference_data(fk_session)

    assert len(await get_trains(fk_session)) == len(trains)
    assert len(await get_train_lines(fk_session)) == expected_train_lines


def load_json(path: Path) -> dict:
    """Return the parsed JSON content of a data file."""
    return json.loads(path.read_text(encoding="utf-8"))


def test_real_trains_file_matches_fleet_specification():
    """The shipped trains.v1.json has the agreed fleet and unique identifiers."""
    trains = load_json(TRAINS_FILE)["trains"]

    assert len(trains) == 73
    fleet = Counter(tuple(train["line_ids"]) for train in trains)
    assert fleet == {("M1", "M2"): 34, ("M3", "M4"): 39}

    for key in ("id", "slug", "beacon_id"):
        values = [train[key] for train in trains]
        assert len(set(values)) == len(values)


def test_real_trains_file_does_not_collide_with_stations_file():
    """No train beacon is a patrol-area beacon, and every train line exists."""
    stations = load_json(STATIONS_FILE)
    trains = load_json(TRAINS_FILE)["trains"]

    area_beacons = {
        area["beacon_id"]
        for station in stations["stations"]
        for area in station["patrol_areas"]
    }
    line_ids = {line["id"] for line in stations["lines"]}

    assert not area_beacons & {train["beacon_id"] for train in trains}
    assert {line for train in trains for line in train["line_ids"]} <= line_ids
