from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models import Line, OverdueLogEntry, PatrolArea, Station, StationLine
from src.db.models.event import Adjustment, Event
from src.db.repository import events, overdue_log, patrol_area, station
from src.domain.coverage import (
    AreaCoverageReport,
    AreaReference,
    OverdueCleared,
    OverdueDetected,
    OverdueEpisode,
    StationCoverageReport,
)
from src.domain.event import EventType
from src.domain.patrol_area import AreaKind
from src.services.station_coverage.overdue_tracker import OverdueTracker

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


def make_event(**overrides: Any) -> Event:
    fields: dict[str, Any] = {
        "event_id": uuid4(),
        "event_type": EventType.CONNECT_EVENT,
        "android_id": UUID("b80fdb46-0666-41e8-883c-0d0bda93f835"),
        "beacon_id": UUID("b80fdb46-0666-41e8-883c-0d0bda93f835"),
        "device_timestamp": TIMESTAMP,
        "server_timestamp": TIMESTAMP,
        "source": "test",
    }
    return Event(**(fields | overrides))


def make_adjustment(**overrides: Any) -> Adjustment:
    fields: dict[str, Any] = {
        "adjustment_id": uuid4(),
        "target_event_id": uuid4(),
        "android_id": UUID("b80fdb46-0666-41e8-883c-0d0bda93f835"),
        "reason": "Forgot to check in",
        "author": "supervisor-1",
        "server_timestamp": TIMESTAMP,
        "source": "test",
        "corrected_fact_type": EventType.START_EVENT,
        "corrected_beacon_id": UUID("b80fdb46-0666-41e8-883c-0d0bda93f835"),
        "corrected_occured_at": TIMESTAMP,
    }
    return Adjustment(**(fields | overrides))


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
async def test_get_station_lines_returns_all_links(session):
    session.add(Station(id="S1", name="Nørreport"))
    session.add(Station(id="S2", name="Kongens Nytorv"))
    session.add(Line(id="M1", name="Metro Line 1"))
    session.add(Line(id="M2", name="Metro Line 2"))
    session.add(StationLine(station_id="S1", line_id="M1"))
    session.add(StationLine(station_id="S2", line_id="M1"))
    session.add(StationLine(station_id="S2", line_id="M2"))
    await session.commit()

    result = await station.get_station_lines(session)

    assert {(sl.station_id, sl.line_id) for sl in result} == {
        ("S1", "M1"),
        ("S2", "M1"),
        ("S2", "M2"),
    }


@pytest.mark.asyncio
async def test_get_station_lines_returns_empty_list_when_no_links(session):
    assert await station.get_station_lines(session) == []


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


OVERDUE_AREA = AreaReference(station_id="S1", area_id="S1-P", kind=AreaKind.PLATFORM)
OVERDUE_AT = TIMESTAMP - timedelta(minutes=5)


def make_detected(**overrides: Any) -> OverdueDetected:
    fields: dict[str, Any] = {
        "area": OVERDUE_AREA,
        "overdue_at": OVERDUE_AT,
        "detected_at": TIMESTAMP,
        "last_covered_at": TIMESTAMP - timedelta(minutes=65),
        "source": "system",
    }
    return OverdueDetected(**(fields | overrides))


def make_cleared(**overrides: Any) -> OverdueCleared:
    fields: dict[str, Any] = {
        "area": OVERDUE_AREA,
        "overdue_at": OVERDUE_AT,
        "cleared_at": TIMESTAMP + timedelta(minutes=2),
        "source": "system",
    }
    return OverdueCleared(**(fields | overrides))


async def overdue_rows(session: AsyncSession) -> dict[str, OverdueLogEntry]:
    result = await session.exec(select(OverdueLogEntry))
    return {row.entry_type: row for row in result.all()}


@pytest.mark.asyncio
async def test_get_entry_ids_returns_empty_set_when_log_is_empty(session):
    assert await overdue_log.get_entry_ids(session) == set()


@pytest.mark.asyncio
async def test_get_entry_ids_returns_stable_ids_of_appended_entries(session):
    detected, cleared = make_detected(), make_cleared()

    await overdue_log.append_entries(session, [detected, cleared])

    assert await overdue_log.get_entry_ids(session) == {
        detected.stable_entry_id,
        cleared.stable_entry_id,
    }


@pytest.mark.asyncio
async def test_append_entries_stores_detected_entry(session):
    await overdue_log.append_entries(session, [make_detected()])

    row = (await overdue_rows(session))["DETECTED"]
    assert row.station_id == "S1"
    assert row.area_id == "S1-P"
    assert row.area_kind == AreaKind.PLATFORM
    assert row.overdue_at == OVERDUE_AT
    assert row.detected_at == TIMESTAMP
    assert row.last_covered_at == TIMESTAMP - timedelta(minutes=65)
    assert row.cleared_at is None
    assert row.source == "system"


@pytest.mark.asyncio
async def test_append_entries_stores_cleared_entry(session):
    await overdue_log.append_entries(session, [make_cleared()])

    row = (await overdue_rows(session))["CLEARED"]
    assert row.overdue_at == OVERDUE_AT
    assert row.cleared_at == TIMESTAMP + timedelta(minutes=2)
    assert row.detected_at is None
    assert row.last_covered_at is None


@pytest.mark.asyncio
async def test_append_entries_rejects_an_entry_already_in_the_log(session):
    await overdue_log.append_entries(session, [make_detected()])

    with pytest.raises(IntegrityError):
        await overdue_log.append_entries(
            session, [make_detected(detected_at=TIMESTAMP + timedelta(minutes=1))]
        )


@pytest.mark.asyncio
async def test_tracking_the_same_episode_again_keeps_the_first_detection(session):
    def reports(now: datetime) -> list[StationCoverageReport]:
        area_report = AreaCoverageReport(
            area=OVERDUE_AREA,
            last_covered_at=TIMESTAMP - timedelta(minutes=65),
            covered_now=False,
            shift_start_time=None,
            current_steward_ids=frozenset(),
            episodes=(OverdueEpisode(overdue_at=OVERDUE_AT, cleared_at=None),),
            time_until_next_needed_patrol=timedelta(minutes=60),
            as_of=now,
        )
        return [StationCoverageReport(station_id="S1", areas=(area_report,))]

    later = TIMESTAMP + timedelta(seconds=5)
    await OverdueTracker().track(session, reports(TIMESTAMP), TIMESTAMP)
    await OverdueTracker().track(session, reports(later), later)

    rows = await overdue_rows(session)
    assert list(rows) == ["DETECTED"]
    assert rows["DETECTED"].detected_at == TIMESTAMP
