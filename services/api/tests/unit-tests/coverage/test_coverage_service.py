from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models import Event, EventType, PatrolArea, Station
from src.models.coverage import CoverageStatus, StationCoverageReport
from src.models.patrol_area import AreaKind
from src.services.coverage.coverage_service import CoverageService
from src.services.coverage.coverage_window import CoverageWindow
from src.services.coverage.interval_builder import IntervalBuilder

NOW = datetime(2026, 10, 8, 12, 0, 0, tzinfo=UTC)
WINDOW = timedelta(minutes=60)
STEWARD = UUID("b80fdb46-0666-41e8-883c-0d0bda93f835")

STATION_A = "STN-A"
STATION_B = "STN-B"
A_PLATFORM_BEACON = UUID("00000000-0000-0000-0000-00000000a001")
A_CONCOURSE_BEACON = UUID("00000000-0000-0000-0000-00000000a002")
B_PLATFORM_BEACON = UUID("00000000-0000-0000-0000-00000000b001")
UNKNOWN_BEACON = UUID("00000000-0000-0000-0000-00000000ffff")


@pytest_asyncio.fixture
async def session() -> AsyncGenerator[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSession(engine) as session:
        # Inserted out of order on purpose: the reports must sort themselves.
        session.add(Station(id=STATION_B, name="Station B"))
        session.add(Station(id=STATION_A, name="Station A"))
        await session.flush()
        session.add(area(B_PLATFORM_BEACON, STATION_B, "B-P", AreaKind.PLATFORM))
        session.add(area(A_PLATFORM_BEACON, STATION_A, "A-P", AreaKind.PLATFORM))
        session.add(area(A_CONCOURSE_BEACON, STATION_A, "A-C", AreaKind.CONCOURSE))
        await session.commit()
        yield session

    await engine.dispose()


@pytest.fixture
def service() -> CoverageService:
    rule = CoverageWindow(
        window=WINDOW,
        min_durations={
            AreaKind.PLATFORM: timedelta(seconds=4),
            AreaKind.CONCOURSE: timedelta(minutes=10),
        },
    )
    return CoverageService(IntervalBuilder(), rule)


def area(beacon_id: UUID, station_id: str | None, area_id: str, kind: AreaKind):
    return PatrolArea(
        beacon_id=beacon_id, station_id=station_id, area_id=area_id, area_kind=kind
    )


async def add_visit(
    session: AsyncSession,
    beacon_id: UUID,
    started_at: datetime,
    ended_at: datetime | None = None,
) -> None:
    session.add(event(EventType.CONNECT_EVENT, beacon_id, started_at))
    if ended_at is not None:
        session.add(event(EventType.DISCONNECT_EVENT, beacon_id, ended_at))
    await session.commit()


def event(event_type: EventType, beacon_id: UUID, at: datetime) -> Event:
    return Event(
        event_id=uuid4(),
        event_type=event_type,
        android_id=STEWARD,
        beacon_id=beacon_id,
        device_timestamp=at,
        server_timestamp=at,
        source="test",
    )


def station(reports: list[StationCoverageReport], station_id: str):
    return next(report for report in reports if report.station_id == station_id)


def area_report(reports: list[StationCoverageReport], station_id: str, area_id: str):
    return next(
        report
        for report in station(reports, station_id).areas
        if report.area.area_id == area_id
    )


async def test_every_patrol_area_gets_a_report_even_without_events(service, session):
    reports = await service.compute_coverage_reports(session, NOW)

    assert [report.station_id for report in reports] == [STATION_A, STATION_B]
    assert [a.area.area_id for a in station(reports, STATION_A).areas] == [
        "A-C",
        "A-P",
    ]
    assert [a.area.area_id for a in station(reports, STATION_B).areas] == ["B-P"]


async def test_area_without_events_is_overdue(service, session):
    reports = await service.compute_coverage_reports(session, NOW)

    assert area_report(reports, STATION_B, "B-P").coverage_status == (
        CoverageStatus.OVERDUE
    )


async def test_visit_counts_only_for_the_area_of_its_beacon(service, session):
    await add_visit(
        session,
        A_PLATFORM_BEACON,
        NOW - timedelta(minutes=10),
        NOW - timedelta(minutes=9),
    )

    reports = await service.compute_coverage_reports(session, NOW)

    a_platform = area_report(reports, STATION_A, "A-P")
    assert a_platform.last_covered_at == NOW - timedelta(minutes=9)
    assert a_platform.coverage_status == CoverageStatus.COMPLIANT
    assert area_report(reports, STATION_A, "A-C").last_covered_at is None
    assert area_report(reports, STATION_B, "B-P").last_covered_at is None


async def test_concourse_and_platform_of_one_station_are_independent(service, session):
    # Long enough for a platform (4 s), too short for a concourse (10 min).
    await add_visit(
        session,
        A_PLATFORM_BEACON,
        NOW - timedelta(minutes=30),
        NOW - timedelta(minutes=25),
    )
    await add_visit(
        session,
        A_CONCOURSE_BEACON,
        NOW - timedelta(minutes=30),
        NOW - timedelta(minutes=25),
    )

    reports = await service.compute_coverage_reports(session, NOW)

    assert area_report(reports, STATION_A, "A-P").last_covered_at is not None
    assert area_report(reports, STATION_A, "A-C").last_covered_at is None


async def test_open_visit_counts_as_covered_now(service, session):
    await add_visit(session, A_PLATFORM_BEACON, NOW - timedelta(minutes=1))

    reports = await service.compute_coverage_reports(session, NOW)

    a_platform = area_report(reports, STATION_A, "A-P")
    assert a_platform.covered_now is True
    assert a_platform.current_steward_ids == frozenset([str(STEWARD)])


async def test_visit_at_a_beacon_without_patrol_area_changes_nothing(service, session):
    before = await service.compute_coverage_reports(session, NOW)
    await add_visit(
        session, UNKNOWN_BEACON, NOW - timedelta(minutes=10), NOW - timedelta(minutes=5)
    )

    after = await service.compute_coverage_reports(session, NOW)

    assert after == before


async def test_area_without_a_station_is_left_out(service, session):
    session.add(area(uuid4(), None, "LOOSE", AreaKind.PLATFORM))
    await session.commit()

    reports = await service.compute_coverage_reports(session, NOW)

    area_ids = {a.area.area_id for report in reports for a in report.areas}
    assert area_ids == {"A-C", "A-P", "B-P"}


async def test_shift_start_time_is_the_baseline_for_unpatrolled_areas(service, session):
    shift_start_time = NOW - timedelta(hours=2)

    reports = await service.compute_coverage_reports(session, NOW, shift_start_time)

    b_platform = area_report(reports, STATION_B, "B-P")
    assert b_platform.overdue_at == shift_start_time + WINDOW
    assert b_platform.coverage_status == CoverageStatus.OVERDUE


async def test_same_data_and_now_give_equal_reports(service, session):
    await add_visit(
        session, A_PLATFORM_BEACON, NOW - timedelta(hours=3), NOW - timedelta(hours=2)
    )
    await add_visit(session, A_CONCOURSE_BEACON, NOW - timedelta(minutes=20))

    first = await service.compute_coverage_reports(session, NOW)
    second = await service.compute_coverage_reports(session, NOW)

    assert first == second
