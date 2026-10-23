from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models import Event, PatrolArea, Station
from src.models.coverage import (
    CoverageStatus,
    OverdueEpisode,
    StationCoverageReport,
)
from src.models.patrol_area import AreaKind
from src.scripts.seed import FIXTURE, load_events
from src.services.coverage.coverage_service import CoverageService
from src.services.coverage.coverage_window import (
    MIN_QUALIFYING_DURATIONS,
    TIME_UNTIL_NEXT_NEEDED_PATROL,
    CoverageWindow,
)
from src.services.coverage.interval_builder import IntervalBuilder

STATION_BEACONS = {
    "STN-2": UUID("550e8400-e29b-41d4-a716-000000000002"),
    "STN-3": UUID("550e8400-e29b-41d4-a716-000000000003"),
    "STN-4": UUID("550e8400-e29b-41d4-a716-000000000004"),
}


def at(hour: int, minute: int, second: int) -> datetime:
    return datetime(2026, 5, 30, hour, minute, second, tzinfo=UTC)


# The updater always passes a shift start, and only then are events after now
# ignored. The fixture's session starts at 03:07:13.
SHIFT_START = at(3, 0, 0)
# After the steward's last event and its session stop at 04:51:40.
AFTER_FIXTURE = at(5, 0, 0)


@pytest_asyncio.fixture
async def session() -> AsyncGenerator[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSession(engine) as session:
        for station_id in STATION_BEACONS:
            session.add(Station(id=station_id, name=station_id))
        await session.flush()
        for station_id, beacon_id in STATION_BEACONS.items():
            session.add(
                PatrolArea(
                    beacon_id=beacon_id,
                    station_id=station_id,
                    area_id=f"{station_id}-P",
                    area_kind=AreaKind.PLATFORM,
                )
            )
        session.add_all(fixture_events())
        await session.commit()
        yield session

    await engine.dispose()


def fixture_events() -> list[Event]:
    # build_events leaves the fixture's ids as strings, which SQLite rejects.
    events = load_events(FIXTURE)
    for event in events:
        event.android_id = UUID(str(event.android_id))
        if event.beacon_id is not None:
            event.beacon_id = UUID(str(event.beacon_id))
    return events


@pytest.fixture
def service() -> CoverageService:
    rule = CoverageWindow(
        time_until_next_needed_patrol=TIME_UNTIL_NEXT_NEEDED_PATROL,
        min_qualifying_durations=MIN_QUALIFYING_DURATIONS,
    )
    return CoverageService(IntervalBuilder(), rule)


async def compute(
    service: CoverageService, session: AsyncSession, now: datetime
) -> list[StationCoverageReport]:
    return await service.compute_coverage_reports(session, now, SHIFT_START)


def platform(reports: list[StationCoverageReport], station_id: str):
    station = next(report for report in reports if report.station_id == station_id)
    (area,) = station.areas
    return area


async def test_fixture_gap_at_station_3_is_one_overdue_episode(service, session):
    reports = await compute(service, session, AFTER_FIXTURE)

    # Coverage of the 03:10:13-03:10:27 visit runs out at 04:10:27. The 04:45:40
    # visit clears it once it qualifies, 10 seconds later.
    assert platform(reports, "STN-3").episodes == (
        OverdueEpisode(overdue_at=at(4, 10, 27), cleared_at=at(4, 45, 50)),
    )


async def test_station_3_is_overdue_during_the_fixture_gap(service, session):
    reports = await compute(service, session, at(4, 30, 0))

    station_3 = platform(reports, "STN-3")
    assert station_3.coverage_status == CoverageStatus.OVERDUE
    assert station_3.overdue_at == at(4, 10, 27)
    assert station_3.overdue_by == timedelta(minutes=19, seconds=33)
    assert station_3.episodes == (
        OverdueEpisode(overdue_at=at(4, 10, 27), cleared_at=None),
    )


async def test_station_3_is_compliant_after_the_fixture_gap(service, session):
    reports = await compute(service, session, AFTER_FIXTURE)

    station_3 = platform(reports, "STN-3")
    assert station_3.coverage_status == CoverageStatus.COMPLIANT
    # The session stop closes the visit, as the steward never disconnects.
    assert station_3.last_covered_at == at(4, 51, 40)
    assert station_3.covered_now is False


async def test_fixture_break_at_station_4_is_overdue_for_the_minutes_past_the_hour(
    service, session
):
    reports = await compute(service, session, AFTER_FIXTURE)

    # The steward leaves station 4 at 03:20:46 and is back at 04:25:59, so the
    # area is overdue from 04:20:46 until that visit qualifies, 10 seconds later.
    assert platform(reports, "STN-4").episodes == (
        OverdueEpisode(overdue_at=at(4, 20, 46), cleared_at=at(4, 26, 9)),
    )


async def test_fixture_signal_blips_do_not_create_episodes(service, session):
    reports = await compute(service, session, at(4, 0, 0))

    # Station 2 drops for 4 s at 03:09:20 and station 4 for 7 s at 03:12:00.
    for station_id in ("STN-2", "STN-4"):
        area = platform(reports, station_id)
        assert area.episodes == ()
        assert area.coverage_status == CoverageStatus.COMPLIANT


async def test_station_2_is_overdue_an_hour_after_its_last_fixture_visit(
    service, session
):
    reports = await compute(service, session, AFTER_FIXTURE)

    station_2 = platform(reports, "STN-2")
    assert station_2.coverage_status == CoverageStatus.OVERDUE
    assert station_2.last_covered_at == at(3, 9, 46)
    assert station_2.episodes == (
        OverdueEpisode(overdue_at=at(4, 9, 46), cleared_at=None),
    )
