"""Unit tests for ComplianceReconstructor.reconstruct."""

from collections.abc import AsyncGenerator
from datetime import UTC, date, datetime, time, timedelta
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models import Event, PatrolArea, Station, Train
from src.domain.compliance import CompliancePicture
from src.domain.coverage import OverdueEpisode
from src.domain.event import EventType
from src.domain.patrol_area import AreaKind
from src.services.compliance.reconstruction import ComplianceReconstructor
from src.services.shared.interval_builder import IntervalBuilder
from src.services.shared.shift_schedule import ShiftSchedule
from src.services.station_coverage.coverage_service import CoverageService
from src.services.station_coverage.coverage_window import (
    MIN_QUALIFYING_DURATIONS,
    TIME_UNTIL_NEXT_NEEDED_PATROL,
    CoverageWindow,
)
from src.services.train_manning.train_manning_evaluator import TrainManningEvaluator
from src.services.train_manning.train_manning_service import TrainManningService

DAY = date(2026, 11, 3)
SHIFT_START = datetime(2026, 11, 2, 23, 0, tzinfo=UTC)
SHIFT_END = datetime(2026, 11, 3, 5, 0, tzinfo=UTC)
AFTER_SHIFT = datetime(2026, 11, 10, 12, 0, tzinfo=UTC)

STEWARD = UUID("660e8400-e29b-41d4-a716-446655440001")
STATION = "STN-A"
AREA_BEACON = UUID("00000000-0000-0000-0000-00000000a001")
TRAIN_BEACON = UUID("00000000-0000-0000-0000-00000000c001")

FIRST_PATROL = SHIFT_START + timedelta(minutes=30)
LATE_PATROL = SHIFT_START + timedelta(hours=2)
LATE_PATROL_RECEIVED = SHIFT_START + timedelta(hours=4)
BEFORE_LATE_PATROL_ARRIVED = SHIFT_START + timedelta(hours=3)


@pytest_asyncio.fixture
async def session() -> AsyncGenerator[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSession(engine) as session:
        session.add(Station(id=STATION, name="Station A"))
        await session.flush()
        session.add(
            PatrolArea(
                beacon_id=AREA_BEACON,
                station_id=STATION,
                area_id="A-P",
                area_kind=AreaKind.PLATFORM,
            )
        )
        session.add(Train(train_id=uuid4(), slug="a29", beacon_id=TRAIN_BEACON))
        await session.commit()
        yield session

    await engine.dispose()


def make_services() -> tuple[CoverageService, TrainManningService]:
    builder = IntervalBuilder()
    rule = CoverageWindow(
        time_until_next_needed_patrol=TIME_UNTIL_NEXT_NEEDED_PATROL,
        min_qualifying_durations=MIN_QUALIFYING_DURATIONS,
    )
    return (
        CoverageService(builder, rule),
        TrainManningService(builder, TrainManningEvaluator()),
    )


@pytest.fixture
def reconstructor() -> ComplianceReconstructor:
    coverage_service, manning_service = make_services()
    return ComplianceReconstructor(
        coverage_service=coverage_service,
        manning_service=manning_service,
        shift_schedule=ShiftSchedule(
            start=time(0, 0),
            end=time(6, 0),
            timezone=ZoneInfo("Europe/Copenhagen"),
        ),
    )


async def add_visit(
    session: AsyncSession,
    beacon_id: UUID,
    started_at: datetime,
    ended_at: datetime,
    received_at: datetime | None = None,
) -> None:
    """Store a connect/disconnect pair; ``received_at`` defaults to on time."""
    for event_type, at in (
        (EventType.CONNECT_EVENT, started_at),
        (EventType.DISCONNECT_EVENT, ended_at),
    ):
        session.add(
            Event(
                event_id=uuid4(),
                event_type=event_type,
                steward_ref=STEWARD,
                beacon_id=beacon_id,
                device_timestamp=at,
                server_timestamp=received_at or at,
                source="test",
            )
        )
    await session.commit()


async def add_on_time_and_late_patrol(session: AsyncSession) -> None:
    await add_visit(
        session, AREA_BEACON, FIRST_PATROL, FIRST_PATROL + timedelta(minutes=1)
    )
    await add_visit(
        session,
        AREA_BEACON,
        LATE_PATROL,
        LATE_PATROL + timedelta(minutes=1),
        received_at=LATE_PATROL_RECEIVED,
    )


def episodes(picture: CompliancePicture) -> tuple[OverdueEpisode, ...]:
    (station,) = picture.stations
    (area,) = station.areas
    return area.episodes


async def test_reconstruct_evaluates_the_shift_on_the_date(session, reconstructor):
    picture = await reconstructor.reconstruct(session, DAY, current_time=AFTER_SHIFT)

    assert picture.shift.start == SHIFT_START
    assert picture.shift.end == SHIFT_END
    assert picture.as_of == SHIFT_END
    assert picture.known_at is None


async def test_reconstruct_without_known_at_counts_late_events(session, reconstructor):
    await add_on_time_and_late_patrol(session)

    picture = await reconstructor.reconstruct(session, DAY, current_time=AFTER_SHIFT)

    first_gap = episodes(picture)[0]
    assert (
        first_gap.cleared_at
        == LATE_PATROL + MIN_QUALIFYING_DURATIONS[AreaKind.PLATFORM]
    )


async def test_reconstruct_with_known_at_leaves_out_events_received_later(
    session, reconstructor
):
    await add_on_time_and_late_patrol(session)

    picture = await reconstructor.reconstruct(
        session,
        DAY,
        current_time=AFTER_SHIFT,
        known_at=BEFORE_LATE_PATROL_ARRIVED,
    )

    assert picture.as_of == BEFORE_LATE_PATROL_ARRIVED
    assert picture.known_at == BEFORE_LATE_PATROL_ARRIVED
    assert episodes(picture) == (
        OverdueEpisode(
            overdue_at=FIRST_PATROL
            + timedelta(minutes=1)
            + TIME_UNTIL_NEXT_NEEDED_PATROL,
            cleared_at=None,
        ),
    )


async def test_reconstruct_with_known_at_matches_the_live_picture_at_that_time(
    session, reconstructor
):
    await add_visit(
        session, AREA_BEACON, FIRST_PATROL, FIRST_PATROL + timedelta(minutes=1)
    )
    await add_visit(
        session, TRAIN_BEACON, SHIFT_START, SHIFT_START + timedelta(hours=2)
    )
    coverage_service, manning_service = make_services()
    live_stations = await coverage_service.compute_coverage_reports(
        session, now=BEFORE_LATE_PATROL_ARRIVED, shift_start_time=SHIFT_START
    )
    live_trains = await manning_service.compute_manning_reports(
        session, now=BEFORE_LATE_PATROL_ARRIVED, shift_start_time=SHIFT_START
    )
    await add_visit(
        session,
        AREA_BEACON,
        LATE_PATROL,
        LATE_PATROL + timedelta(minutes=1),
        received_at=LATE_PATROL_RECEIVED,
    )

    picture = await reconstructor.reconstruct(
        session,
        DAY,
        current_time=AFTER_SHIFT,
        known_at=BEFORE_LATE_PATROL_ARRIVED,
    )

    assert picture.stations == tuple(live_stations)
    assert picture.trains == tuple(live_trains)


async def test_reconstruct_is_repeatable(session, reconstructor):
    await add_on_time_and_late_patrol(session)

    first = await reconstructor.reconstruct(session, DAY, current_time=AFTER_SHIFT)
    second = await reconstructor.reconstruct(session, DAY, current_time=AFTER_SHIFT)

    assert first == second


async def test_reconstruct_measures_train_manning_over_the_whole_shift(
    session, reconstructor
):
    await add_visit(
        session, TRAIN_BEACON, SHIFT_START, SHIFT_START + timedelta(hours=5)
    )

    picture = await reconstructor.reconstruct(session, DAY, current_time=AFTER_SHIFT)

    (train,) = picture.trains
    assert train.running_time == timedelta(hours=6)
    assert train.manned_time == timedelta(hours=5)


async def test_reconstruct_shift_still_running_is_evaluated_up_to_current_time(
    session, reconstructor
):
    during_shift = SHIFT_START + timedelta(hours=1)

    picture = await reconstructor.reconstruct(session, DAY, current_time=during_shift)

    assert picture.as_of == during_shift


async def test_reconstruct_shift_not_started_raises(session, reconstructor):
    with pytest.raises(ValueError, match="had not started"):
        await reconstructor.reconstruct(
            session, DAY, current_time=SHIFT_START - timedelta(minutes=1)
        )


async def test_reconstruct_known_at_before_shift_start_raises(session, reconstructor):
    with pytest.raises(ValueError, match="had not started"):
        await reconstructor.reconstruct(
            session,
            DAY,
            current_time=AFTER_SHIFT,
            known_at=SHIFT_START - timedelta(minutes=1),
        )
