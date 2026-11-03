"""Tests for building a steward's patrol records from shift events."""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from src.api.v2.routers.patrol_record import build_records
from src.api.v2.schemas.patrol_record import AreaType, Status
from src.db.models import Event, Line, PatrolArea, Station, StationLine
from src.domain.event import EventType
from src.domain.patrol_area import AreaKind

SHIFT_START = datetime(2026, 10, 8, 12, 0, tzinfo=UTC)
STEWARD_ANDROID_ID = UUID("b80fdb46-0666-41e8-883c-0d0bda93f835")
OTHER_ANDROID_ID = UUID("c1d0e2f3-4a5b-4c6d-8e9f-0a1b2c3d4e5f")
PLATFORM_BEACON_ID = UUID("d2e1f0a1-3b4c-4d5e-9f0a-1b2c3d4e5f6a")
CONCOURSE_BEACON_ID = UUID("e3f2a1b2-4c5d-4e6f-8a1b-2c3d4e5f6a7b")
UNKNOWN_BEACON_ID = UUID("f4a3b2c3-5d6e-4f7a-9b2c-3d4e5f6a7b8c")


@pytest_asyncio.fixture
async def session() -> AsyncGenerator[AsyncSession]:
    """Yield an in-memory database with one station and two patrol areas."""
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSession(engine) as session:
        session.add(Station(id="S1", name="Nørreport"))
        session.add(Line(id="M2", name="M2"))
        session.add(Line(id="M1", name="M1"))
        session.add(StationLine(station_id="S1", line_id="M2"))
        session.add(StationLine(station_id="S1", line_id="M1"))
        await session.flush()
        session.add(
            PatrolArea(
                beacon_id=PLATFORM_BEACON_ID,
                station_id="S1",
                area_id="platform-a",
                area_kind=AreaKind.PLATFORM,
            )
        )
        session.add(
            PatrolArea(
                beacon_id=CONCOURSE_BEACON_ID,
                station_id="S1",
                area_id="concourse-a",
                area_kind=AreaKind.CONCOURSE,
            )
        )
        await session.commit()
        yield session

    await engine.dispose()


async def add_event(session: AsyncSession, **overrides: Any) -> None:
    """Store a steward CONNECT event at shift start, with `overrides` applied."""
    fields: dict[str, Any] = {
        "event_id": uuid4(),
        "event_type": EventType.CONNECT_EVENT,
        "android_id": STEWARD_ANDROID_ID,
        "beacon_id": PLATFORM_BEACON_ID,
        "device_timestamp": SHIFT_START,
        "server_timestamp": SHIFT_START,
        "source": "test",
    }
    session.add(Event(**(fields | overrides)))
    await session.commit()


async def start_shift(session: AsyncSession, at: datetime = SHIFT_START) -> None:
    """Store a shift START event for the steward at `at`."""
    await add_event(
        session,
        event_type=EventType.START_EVENT,
        beacon_id=None,
        device_timestamp=at,
    )


async def connect(session: AsyncSession, offset_secs: int, **overrides: Any) -> None:
    """Store a CONNECT event `offset_secs` after shift start."""
    await add_event(
        session,
        device_timestamp=SHIFT_START + timedelta(seconds=offset_secs),
        **overrides,
    )


async def disconnect(session: AsyncSession, offset_secs: int, **overrides: Any) -> None:
    """Store a DISCONNECT event `offset_secs` after shift start."""
    await add_event(
        session,
        event_type=EventType.DISCONNECT_EVENT,
        device_timestamp=SHIFT_START + timedelta(seconds=offset_secs),
        **overrides,
    )


@pytest.mark.asyncio
async def test_build_records_is_empty_without_shift_start(session):
    """Events count only once the steward has started a shift."""
    await connect(session, 10)

    result = await build_records(session, STEWARD_ANDROID_ID)

    assert result.records == []


@pytest.mark.asyncio
async def test_build_records_pairs_connect_and_disconnect(session):
    """A connect followed by a disconnect becomes one closed record."""
    await start_shift(session)
    await connect(session, 10)
    await disconnect(session, 55)

    result = await build_records(session, STEWARD_ANDROID_ID)

    [record] = result.records
    assert record.android_id == STEWARD_ANDROID_ID
    assert record.beacon_id == PLATFORM_BEACON_ID
    assert record.started_at == SHIFT_START + timedelta(seconds=10)
    assert record.ended_at == SHIFT_START + timedelta(seconds=55)
    assert record.duration_secs == 45
    assert record.min_patrol_duration_secs == 10
    assert record.patrolled is True
    assert record.status == Status.CLOSED


@pytest.mark.asyncio
async def test_build_records_resolves_area(session):
    """The record's area is named after its station and lists its lines."""
    await start_shift(session)
    await connect(session, 10)

    result = await build_records(session, STEWARD_ANDROID_ID)

    area = result.records[0].area
    assert area.area_id == "platform-a"
    assert area.name == "Nørreport platform"
    assert area.line == ["M1", "M2"]
    assert area.station_id == "S1"
    assert area.area_type == AreaType.PLATFORM


@pytest.mark.asyncio
async def test_build_records_leaves_unmatched_connect_open(session):
    """A connect with no disconnect yet becomes an open record."""
    await start_shift(session)
    await connect(session, 10)

    result = await build_records(session, STEWARD_ANDROID_ID)

    [record] = result.records
    assert record.ended_at is None
    assert record.duration_secs == int(
        (result.time - record.started_at).total_seconds()
    )
    assert record.patrolled is True
    assert record.status == Status.OPEN


@pytest.mark.asyncio
async def test_build_records_marks_short_visit_not_patrolled(session):
    """A visit shorter than the area's minimum duration is not patrolled."""
    await start_shift(session)
    await connect(session, 10, beacon_id=CONCOURSE_BEACON_ID)
    await disconnect(session, 25, beacon_id=CONCOURSE_BEACON_ID)

    result = await build_records(session, STEWARD_ANDROID_ID)

    [record] = result.records
    assert record.duration_secs == 15
    assert record.min_patrol_duration_secs == 20
    assert record.patrolled is False


@pytest.mark.asyncio
async def test_build_records_excludes_events_before_shift_start(session):
    """Events from before the latest shift start are ignored."""
    await connect(session, -100)
    await disconnect(session, -50)
    await start_shift(session)

    result = await build_records(session, STEWARD_ANDROID_ID)

    assert result.records == []


@pytest.mark.asyncio
async def test_build_records_excludes_other_stewards(session):
    """Only the requested steward's events are used."""
    await start_shift(session)
    await connect(session, 10, android_id=OTHER_ANDROID_ID)

    result = await build_records(session, STEWARD_ANDROID_ID)

    assert result.records == []


@pytest.mark.asyncio
async def test_build_records_ignores_disconnect_without_connect(session):
    """A disconnect with no earlier connect produces no record."""
    await start_shift(session)
    await disconnect(session, 10)

    result = await build_records(session, STEWARD_ANDROID_ID)

    assert result.records == []


@pytest.mark.asyncio
async def test_build_records_skips_beacons_without_area(session):
    """Events from beacons with no patrol area produce no record."""
    await start_shift(session)
    await connect(session, 10, beacon_id=UNKNOWN_BEACON_ID)
    await disconnect(session, 50, beacon_id=UNKNOWN_BEACON_ID)

    result = await build_records(session, STEWARD_ANDROID_ID)

    assert result.records == []


@pytest.mark.asyncio
async def test_build_records_skips_areas_of_unknown_stations(session):
    """An area whose station is not stored is skipped instead of failing."""
    session.add(
        PatrolArea(
            beacon_id=UNKNOWN_BEACON_ID,
            station_id="MISSING",
            area_id="platform-x",
            area_kind=AreaKind.PLATFORM,
        )
    )
    await session.commit()
    await start_shift(session)
    await connect(session, 10, beacon_id=UNKNOWN_BEACON_ID)
    await connect(session, 20)

    result = await build_records(session, STEWARD_ANDROID_ID)

    [record] = result.records
    assert record.beacon_id == PLATFORM_BEACON_ID


@pytest.mark.asyncio
async def test_build_records_returns_most_recent_first(session):
    """Records are sorted by start time, most recent first."""
    await start_shift(session)
    await connect(session, 10)
    await disconnect(session, 30)
    await connect(session, 40, beacon_id=CONCOURSE_BEACON_ID)
    await connect(session, 60)

    result = await build_records(session, STEWARD_ANDROID_ID)

    assert [record.started_at for record in result.records] == [
        SHIFT_START + timedelta(seconds=60),
        SHIFT_START + timedelta(seconds=40),
        SHIFT_START + timedelta(seconds=10),
    ]
    assert [record.status for record in result.records] == [
        Status.OPEN,
        Status.OPEN,
        Status.CLOSED,
    ]
