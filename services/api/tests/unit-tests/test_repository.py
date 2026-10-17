from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

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
STEWARD_ANDROID_ID = UUID("b80fdb46-0666-41e8-883c-0d0bda93f835")
OTHER_ANDROID_ID = UUID("c1d0e2f3-4a5b-4c6d-8e9f-0a1b2c3d4e5f")
OPEN_BEACON_ID = UUID("d2e1f0a1-3b4c-4d5e-9f0a-1b2c3d4e5f6a")


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
        "android_id": UUID("b80fdb46-0666-41e8-883c-0d0bda93f835"),
        "beacon_id": UUID("b80fdb46-0666-41e8-883c-0d0bda93f835"),
        "device_timestamp": TIMESTAMP,
        "server_timestamp": TIMESTAMP,
        "source": "test",
    }
    return EventModel(**(fields | overrides))


def make_adjustment(**overrides: Any) -> AdjustmentModel:
    fields: dict[str, Any] = {
        "adjustment_id": uuid4(),
        "target_event_id": uuid4(),
        "android_id": UUID("b80fdb46-0666-41e8-883c-0d0bda93f835"),
        "reason": "Forgot to check in",
        "author": "supervisor-1",
        "server_timestamp": TIMESTAMP,
        "source": "test",
        "corrected_fact": CorrectedFact(
            fact_type=EventType.START_EVENT,
            beacon_id=UUID("b80fdb46-0666-41e8-883c-0d0bda93f835"),
            occurred_at=TIMESTAMP,
        ),
    }
    return AdjustmentModel(**(fields | overrides))


@pytest.mark.asyncio
async def test_get_station_returns_matching_station(session):
    session.add(Station(id="S1", name="Nørreport"))
    session.add(Station(id="S2", name="Kongens Nytorv"))
    await session.commit()

    result = await station.get_station(session, "S1")

    assert result.name == "Nørreport"


@pytest.mark.asyncio
async def test_get_station_raises_when_missing(session):
    with pytest.raises(NoResultFound):
        await station.get_station(session, "does-not-exist")


@pytest.mark.asyncio
async def test_get_stations_returns_all_stations(session):
    session.add(Station(id="S1", name="Nørreport"))
    session.add(Station(id="S2", name="Kongens Nytorv"))
    await session.commit()

    result = await station.get_stations(session)

    assert {s.id for s in result} == {"S1", "S2"}


@pytest.mark.asyncio
async def test_get_stations_returns_empty_list_when_no_stations(session):
    assert await station.get_stations(session) == []


@pytest.mark.asyncio
async def test_get_patrol_area_returns_matching_area(session):
    beacon_id = uuid4()
    session.add(Station(id="S1", name="Nørreport"))
    session.add(
        PatrolArea(
            beacon_id=beacon_id,
            station_id="S1",
            area_id="S1-platform",
            area_kind=AreaKind.PLATFORM,
        ),
    )
    await session.commit()

    result = await patrol_area.get_patrol_area(session, beacon_id)

    assert result.station_id == "S1"
    assert result.area_kind == AreaKind.PLATFORM


@pytest.mark.asyncio
async def test_get_patrol_areas_returns_all_areas(session):
    session.add(Station(id="S1", name="Nørreport"))
    session.add(
        PatrolArea(
            beacon_id=uuid4(),
            station_id="S1",
            area_id="S1-platform",
            area_kind=AreaKind.PLATFORM,
        ),
    )
    session.add(
        PatrolArea(
            beacon_id=uuid4(),
            station_id="S1",
            area_id="S1-concourse",
            area_kind=AreaKind.CONCOURSE,
        ),
    )
    await session.commit()

    result = await patrol_area.get_patrol_areas(session)

    assert {a.area_id for a in result} == {"S1-platform", "S1-concourse"}


@pytest.mark.asyncio
async def test_insert_event_can_be_read_back(session):
    event = make_event(event_type=EventType.START_EVENT, beacon_id=None)
    event_id = event.event_id

    await events.insert_event(session, event)
    result = await events.get_event(session, event_id)

    assert result.event_type == EventType.START_EVENT
    assert result.android_id == event.android_id
    assert result.beacon_id is None
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
async def test_reconnect_to_same_beacon_is_stored_as_new_event(session):
    connect = make_event(event_type=EventType.CONNECT_EVENT)
    disconnect = make_event(
        event_type=EventType.DISCONNECT_EVENT,
        device_timestamp=TIMESTAMP + timedelta(minutes=3),
    )
    reconnect = make_event(
        event_type=EventType.CONNECT_EVENT,
        device_timestamp=TIMESTAMP + timedelta(minutes=5),
    )

    for event in (connect, disconnect, reconnect):
        await events.insert_event(session, event)
    result = sorted(await events.get_events(session), key=lambda e: e.device_timestamp)

    assert [e.event_type for e in result] == [
        EventType.CONNECT_EVENT,
        EventType.DISCONNECT_EVENT,
        EventType.CONNECT_EVENT,
    ]
    assert {(e.android_id, e.beacon_id) for e in result} == {
        (connect.android_id, connect.beacon_id),
    }
    assert result[0].event_id != result[2].event_id
    assert result[2].device_timestamp == TIMESTAMP + timedelta(minutes=5)


@pytest.mark.asyncio
async def test_event_recieved_after_stop_still_stored(session):
    start = make_event(event_type=EventType.START_EVENT)
    stop = make_event(
        event_type=EventType.STOP_EVENT,
        device_timestamp=TIMESTAMP + timedelta(minutes=5),
        server_timestamp=TIMESTAMP + timedelta(minutes=5),
    )
    connection_event = make_event(
        event_type=EventType.CONNECT_EVENT,
        device_timestamp=TIMESTAMP + timedelta(minutes=3),
        server_timestamp=TIMESTAMP + timedelta(minutes=7),
    )

    for event in (start, stop, connection_event):
        await events.insert_event(session, event)
    # This query is supposed to mock how a query to build a report could be made based
    # on ordering of the device timestamp
    result = sorted(await events.get_events(session), key=lambda e: e.device_timestamp)
    connection = result[1]
    assert connection.device_timestamp == connection_event.device_timestamp


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


@pytest.mark.asyncio
async def test_get_open_connections_returns_unmatched_connects(session):
    open_connect = make_event(beacon_id=OPEN_BEACON_ID)

    await events.insert_event(session, open_connect)

    result = await events.get_open_connections(session, STEWARD_ANDROID_ID)

    assert [open_connection.event_id for open_connection in result] == [
        open_connect.event_id
    ]


@pytest.mark.asyncio
async def test_get_open_connections_ignores_disconnects_without_connect(session):
    await events.insert_event(
        session, make_event(event_type=EventType.DISCONNECT_EVENT)
    )

    assert await events.get_open_connections(session, STEWARD_ANDROID_ID) == []


@pytest.mark.asyncio
async def test_get_open_connections_excludes_disconnected_beacons(session):
    await events.insert_event(
        session, make_event(device_timestamp=datetime(2026, 10, 8, 10, tzinfo=UTC))
    )
    await events.insert_event(
        session,
        make_event(
            event_type=EventType.DISCONNECT_EVENT,
            device_timestamp=datetime(2026, 10, 8, 11, tzinfo=UTC),
        ),
    )

    assert await events.get_open_connections(session, STEWARD_ANDROID_ID) == []


@pytest.mark.asyncio
async def test_get_open_connections_returns_reopened_connects(session):
    reopened = make_event(device_timestamp=datetime(2026, 10, 8, 12, tzinfo=UTC))
    await events.insert_event(
        session, make_event(device_timestamp=datetime(2026, 10, 8, 10, tzinfo=UTC))
    )
    await events.insert_event(
        session,
        make_event(
            event_type=EventType.DISCONNECT_EVENT,
            device_timestamp=datetime(2026, 10, 8, 11, tzinfo=UTC),
        ),
    )
    await events.insert_event(session, reopened)

    result = await events.get_open_connections(session, STEWARD_ANDROID_ID)

    assert [open_connection.event_id for open_connection in result] == [
        reopened.event_id
    ]


@pytest.mark.asyncio
async def test_get_open_connections_only_returns_events_of_android_id(session):
    await events.insert_event(session, make_event(android_id=OTHER_ANDROID_ID))

    assert await events.get_open_connections(session, STEWARD_ANDROID_ID) == []


@pytest.mark.asyncio
async def test_get_open_connections_returns_one_event_per_beacon(session):
    await events.insert_event(
        session, make_event(device_timestamp=datetime(2026, 10, 8, 10, tzinfo=UTC))
    )
    latest = make_event(device_timestamp=datetime(2026, 10, 8, 11, tzinfo=UTC))
    await events.insert_event(session, latest)

    result = await events.get_open_connections(session, STEWARD_ANDROID_ID)

    assert [open_connection.event_id for open_connection in result] == [latest.event_id]
