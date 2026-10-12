from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.repository import events, patrol_area, station
from src.models import PatrolArea, Station
from src.models.event import AdjustmentModel, CorrectedFact, EventModel, EventType
from src.models.patrol_area import AreaKind

TIMESTAMP = datetime(2026, 10, 8, 12, 0, tzinfo=UTC)


@pytest_asyncio.fixture
async def session() -> AsyncGenerator[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSession(engine) as session:
        yield session

    await engine.dispose()


def make_event(**overrides: Any) -> EventModel:
    fields: dict[str, Any] = {
        "event_id": uuid4(),
        "event_type": EventType.CONNECT_EVENT,
        "actor": "steward-1",
        "beacon": "beacon-1",
        "device_timestamp": TIMESTAMP,
        "server_timestamp": TIMESTAMP,
        "source": "test",
    }
    return EventModel(**(fields | overrides))


def make_adjustment(**overrides: Any) -> AdjustmentModel:
    fields: dict[str, Any] = {
        "adjustment_id": uuid4(),
        "target_event_id": uuid4(),
        "actor": "steward-1",
        "reason": "Forgot to check in",
        "author": "supervisor-1",
        "server_timestamp": TIMESTAMP,
        "source": "test",
        "corrected_fact": CorrectedFact(
            fact_type=EventType.START_EVENT,
            beacon_id="beacon-1",
            occurred_at=TIMESTAMP,
        ),
    }
    return AdjustmentModel(**(fields | overrides))


@pytest.mark.asyncio
async def test_get_station_returns_matching_station(session):
    session.add(Station(id="S1", name="Nørreport", line_ids=["M1", "M2"]))
    session.add(Station(id="S2", name="Kongens Nytorv", line_ids=["M3"]))
    await session.commit()

    result = await station.get_station(session, "S1")

    assert result.name == "Nørreport"
    assert result.line_ids == ["M1", "M2"]


@pytest.mark.asyncio
async def test_get_station_raises_when_missing(session):
    with pytest.raises(NoResultFound):
        await station.get_station(session, "does-not-exist")


@pytest.mark.asyncio
async def test_get_stations_returns_all_stations(session):
    session.add(Station(id="S1", name="Nørreport", line_ids=["M1"]))
    session.add(Station(id="S2", name="Kongens Nytorv", line_ids=["M3"]))
    await session.commit()

    result = await station.get_stations(session)

    assert {s.id for s in result} == {"S1", "S2"}


@pytest.mark.asyncio
async def test_get_stations_returns_empty_list_when_no_stations(session):
    assert await station.get_stations(session) == []


@pytest.mark.asyncio
async def test_get_patrol_area_returns_matching_area(session):
    beacon_id = uuid4()
    session.add(Station(id="S1", name="Nørreport", line_ids=["M1"]))
    session.add(
        PatrolArea(
            beacon_id=beacon_id,
            station_id="S1",
            id="S1-platform",
            area_kind=AreaKind.PLATFORM,
        ),
    )
    await session.commit()

    result = await patrol_area.get_patrol_area(session, beacon_id)

    assert result.station_id == "S1"
    assert result.area_kind == AreaKind.PLATFORM


@pytest.mark.asyncio
async def test_get_patrol_areas_returns_all_areas(session):
    session.add(Station(id="S1", name="Nørreport", line_ids=["M1"]))
    session.add(
        PatrolArea(
            beacon_id=uuid4(),
            station_id="S1",
            id="S1-platform",
            area_kind=AreaKind.PLATFORM,
        ),
    )
    session.add(
        PatrolArea(
            beacon_id=uuid4(),
            station_id="S1",
            id="S1-concourse",
            area_kind=AreaKind.CONCOURSE,
        ),
    )
    await session.commit()

    result = await patrol_area.get_patrol_areas(session)

    assert {a.id for a in result} == {"S1-platform", "S1-concourse"}


@pytest.mark.asyncio
async def test_insert_event_can_be_read_back(session):
    event = make_event(event_type=EventType.START_EVENT, beacon=None)
    event_id = event.event_id

    await events.insert_event(session, event)
    result = await events.get_event(session, event_id)

    assert result.event_type == EventType.START_EVENT
    assert result.actor == "steward-1"
    assert result.beacon is None
    assert result.source == "test"


@pytest.mark.asyncio
async def test_get_event_raises_when_missing(session):
    with pytest.raises(NoResultFound):
        await events.get_event(session, uuid4())


@pytest.mark.asyncio
async def test_get_events_returns_all_inserted_events(session):
    first = make_event()
    second = make_event(event_type=EventType.DISCONNECT_EVENT)
    expected_ids = {first.event_id, second.event_id}

    await events.insert_event(session, first)
    await events.insert_event(session, second)
    result = await events.get_events(session)

    assert {e.event_id for e in result} == expected_ids


@pytest.mark.asyncio
async def test_insert_adjustment_can_be_read_back(session):
    target_event_id = uuid4()
    adjustment = make_adjustment(target_event_id=target_event_id)
    adjustment_id = adjustment.adjustment_id

    await events.insert_adjustment(session, adjustment)
    result = await events.get_adjustment(session, adjustment_id)

    assert result.target_event_id == target_event_id
    assert result.reason == "Forgot to check in"
    assert result.corrected_fact_type == EventType.START_EVENT
    assert result.source == "test"


@pytest.mark.asyncio
async def test_get_adjustments_returns_all_inserted_adjustments(session):
    first = make_adjustment()
    second = make_adjustment(target_event_id=None)
    expected_ids = {first.adjustment_id, second.adjustment_id}

    await events.insert_adjustment(session, first)
    await events.insert_adjustment(session, second)
    result = await events.get_adjustments(session)

    assert {a.adjustment_id for a in result} == expected_ids
