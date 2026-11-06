"""Unit tests for TrainManningService.compute_manning_reports."""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models import Event, Line, Train, TrainLine
from src.domain.event import EventType
from src.services.shared.interval_builder import IntervalBuilder
from src.services.train_manning.train_manning_evaluator import TrainManningEvaluator
from src.services.train_manning.train_manning_service import TrainManningService

T0 = datetime(2026, 10, 8, 10, 0, 0, tzinfo=UTC)
T1 = T0 + timedelta(hours=1)
T2 = T0 + timedelta(hours=2)

STEWARD = UUID("660e8400-e29b-41d4-a716-446655440001")
TRAIN_ID = UUID("770e8400-e29b-41d4-a716-446655440001")
BEACON_ID = UUID("550e8400-e29b-41d4-a716-446655440000")
OTHER_BEACON_ID = UUID("550e8400-e29b-41d4-a716-446655440099")


@pytest_asyncio.fixture
async def session() -> AsyncGenerator[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSession(engine) as session:
        session.add(Train(train_id=TRAIN_ID, slug="a29", beacon_id=BEACON_ID))
        for line_id in ("M1", "M2"):
            session.add(Line(id=line_id, name=line_id))
            session.add(TrainLine(train_id=TRAIN_ID, line_id=line_id))
        await session.commit()
        yield session

    await engine.dispose()


def make_service() -> TrainManningService:
    return TrainManningService(IntervalBuilder(), TrainManningEvaluator())


async def add_event(
    session: AsyncSession,
    event_type: EventType,
    beacon_id: UUID,
    timestamp: datetime,
) -> None:
    session.add(
        Event(
            event_id=uuid4(),
            event_type=event_type,
            android_id=STEWARD,
            beacon_id=beacon_id,
            device_timestamp=timestamp,
            server_timestamp=timestamp,
            source="test",
        )
    )
    await session.commit()


async def test_train_without_events_is_unmanned(session):
    await add_event(session, EventType.CONNECT_EVENT, OTHER_BEACON_ID, T0)

    reports = await make_service().compute_manning_reports(
        session, now=T1, shift_start_time=T0
    )

    assert len(reports) == 1
    assert reports[0].manned_now is False
    assert reports[0].current_steward_ids == frozenset()
    assert reports[0].manned_time.total_seconds() == 0


async def test_connect_marks_the_train_manned(session):
    await add_event(session, EventType.CONNECT_EVENT, BEACON_ID, T0)

    reports = await make_service().compute_manning_reports(
        session, now=T1, shift_start_time=T0
    )

    assert len(reports) == 1
    report = reports[0]
    assert report.train.train_id == TRAIN_ID
    assert report.train.slug == "a29"
    assert report.train.line_ids == frozenset({"M1", "M2"})
    assert report.manned_now is True
    assert report.current_steward_ids == frozenset({STEWARD})
    assert report.manned_time == T1 - T0


async def test_disconnect_makes_the_train_unmanned(session):
    await add_event(session, EventType.CONNECT_EVENT, BEACON_ID, T0)
    await add_event(session, EventType.DISCONNECT_EVENT, BEACON_ID, T1)

    reports = await make_service().compute_manning_reports(
        session, now=T2, shift_start_time=T0
    )

    assert reports[0].manned_now is False
    assert reports[0].current_steward_ids == frozenset()
    assert reports[0].manned_time == T1 - T0
