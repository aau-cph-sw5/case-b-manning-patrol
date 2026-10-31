from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models import Event, Line, Train, TrainLine
from src.domain.event import EventType
from src.services.station_coverage.interval_builder import IntervalBuilder
from src.services.train_manning.train_manning_evaluator import TrainManningEvaluator
from src.services.train_manning.train_manning_service import TrainManningService

NOW = datetime(2026, 10, 8, 12, 0, 0, tzinfo=UTC)
SHIFT_START = datetime(2026, 10, 8, 0, 0, 0, tzinfo=UTC)

STEWARD_A = UUID("b80fdb46-0666-41e8-883c-0d0bda93f835")
STEWARD_B = UUID("c91fec57-1777-52f9-994d-1e1ceb04a946")
TRAIN_1_ID = UUID("10000000-0000-0000-0000-000000000001")
TRAIN_2_ID = UUID("10000000-0000-0000-0000-000000000002")
TRAIN_1_BEACON = UUID("00000000-0000-0000-0000-00000000a001")
TRAIN_2_BEACON = UUID("00000000-0000-0000-0000-00000000a002")
OTHER_BEACON = UUID("00000000-0000-0000-0000-00000000ffff")


@pytest_asyncio.fixture
async def session() -> AsyncGenerator[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSession(engine) as session:
        yield session

    await engine.dispose()


@pytest.fixture
def service() -> TrainManningService:
    return TrainManningService(IntervalBuilder(), TrainManningEvaluator())


def add_train(
    session: AsyncSession,
    train: Train | None = None,
    lines: tuple[str, ...] = ("M1", "M2"),
) -> None:
    train = train or Train(id=TRAIN_1_ID, slug="a29", beacon_id=TRAIN_1_BEACON)
    session.add(train)
    for line_id in lines:
        session.add(Line(id=line_id, name=line_id))
        session.add(TrainLine(train_id=train.id, line_id=line_id))


def add_event(
    session: AsyncSession,
    event_type: EventType,
    timestamp: datetime,
    beacon_id: UUID | None = TRAIN_1_BEACON,
    android_id: UUID = STEWARD_A,
) -> None:
    session.add(
        Event(
            event_id=uuid4(),
            event_type=event_type,
            android_id=android_id,
            beacon_id=beacon_id,
            device_timestamp=timestamp,
            server_timestamp=timestamp,
            source="test",
        )
    )


async def compute(service, session):
    return await service.compute_manning_reports(
        session, NOW, shift_start_time=SHIFT_START
    )


async def test_empty_train_table_returns_no_reports(service, session):
    assert await compute(service, session) == []


async def test_train_without_events_is_unmanned(service, session):
    add_train(session)
    await session.commit()

    reports = await compute(service, session)

    assert len(reports) == 1
    report = reports[0]
    assert report.train.id == TRAIN_1_ID
    assert report.train.slug == "a29"
    assert report.train.line_ids == frozenset({"M1", "M2"})
    assert report.manned_now is False
    assert report.current_steward_ids == frozenset()
    assert report.manned_time == timedelta(0)
    assert report.running_time == NOW - SHIFT_START


async def test_open_connect_marks_train_manned(service, session):
    add_train(session)
    connect_at = datetime(2026, 10, 8, 10, 0, 0, tzinfo=UTC)
    add_event(session, EventType.CONNECT_EVENT, connect_at)
    await session.commit()

    reports = await compute(service, session)

    assert reports[0].manned_now is True
    assert reports[0].current_steward_ids == frozenset({STEWARD_A})
    assert reports[0].manned_time == NOW - connect_at


async def test_closed_interval_accumulates_time_but_is_not_manned_now(service, session):
    add_train(session)
    connect_at = datetime(2026, 10, 8, 10, 0, 0, tzinfo=UTC)
    disconnect_at = datetime(2026, 10, 8, 11, 30, 0, tzinfo=UTC)
    add_event(session, EventType.CONNECT_EVENT, connect_at)
    add_event(session, EventType.DISCONNECT_EVENT, disconnect_at)
    await session.commit()

    reports = await compute(service, session)

    assert reports[0].manned_now is False
    assert reports[0].current_steward_ids == frozenset()
    assert reports[0].manned_time == timedelta(hours=1, minutes=30)


async def test_overlapping_stewards_are_unioned(service, session):
    add_train(session)
    add_event(
        session,
        EventType.CONNECT_EVENT,
        datetime(2026, 10, 8, 1, 0, 0, tzinfo=UTC),
        android_id=STEWARD_A,
    )
    add_event(
        session,
        EventType.CONNECT_EVENT,
        datetime(2026, 10, 8, 2, 0, 0, tzinfo=UTC),
        android_id=STEWARD_B,
    )
    add_event(
        session,
        EventType.DISCONNECT_EVENT,
        datetime(2026, 10, 8, 3, 0, 0, tzinfo=UTC),
        android_id=STEWARD_A,
    )
    await session.commit()

    reports = await compute(service, session)

    # Union of 01:00-03:00 (A) and 02:00-now (B) is 01:00-now.
    assert reports[0].manned_time == NOW - datetime(2026, 10, 8, 1, 0, 0, tzinfo=UTC)
    assert reports[0].manned_now is True
    assert reports[0].current_steward_ids == frozenset({STEWARD_B})


async def test_interval_starting_before_shift_is_clamped(service, session):
    add_train(session)
    add_event(
        session,
        EventType.CONNECT_EVENT,
        SHIFT_START - timedelta(hours=2),
    )
    await session.commit()

    reports = await compute(service, session)

    assert reports[0].manned_now is True
    assert reports[0].manned_time == NOW - SHIFT_START


async def test_events_for_other_beacons_do_not_leak(service, session):
    add_train(session)
    add_event(
        session,
        EventType.CONNECT_EVENT,
        datetime(2026, 10, 8, 10, 0, 0, tzinfo=UTC),
        beacon_id=OTHER_BEACON,
    )
    await session.commit()

    reports = await compute(service, session)

    assert reports[0].manned_now is False
    assert reports[0].manned_time == timedelta(0)


async def test_every_train_gets_exactly_one_report(service, session):
    add_train(session)
    add_train(
        session,
        train=Train(id=TRAIN_2_ID, slug="b07", beacon_id=TRAIN_2_BEACON),
        lines=("M3",),
    )
    add_event(
        session,
        EventType.CONNECT_EVENT,
        datetime(2026, 10, 8, 10, 0, 0, tzinfo=UTC),
        beacon_id=TRAIN_2_BEACON,
    )
    await session.commit()

    reports = await compute(service, session)

    by_id = {report.train.id: report for report in reports}
    assert set(by_id) == {TRAIN_1_ID, TRAIN_2_ID}
    assert by_id[TRAIN_1_ID].manned_now is False
    assert by_id[TRAIN_2_ID].manned_now is True
    assert by_id[TRAIN_2_ID].train.line_ids == frozenset({"M3"})
