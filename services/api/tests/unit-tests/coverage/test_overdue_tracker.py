from datetime import datetime, timedelta
from typing import cast

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.coverage import (
    AreaCoverageReport,
    AreaReference,
    OverdueCleared,
    OverdueDetected,
    OverdueEpisode,
    StationCoverageReport,
)
from src.models.patrol_area import AreaKind
from src.services.station_coverage import overdue_tracker
from src.services.station_coverage.overdue_tracker import OverdueTracker

NOW = datetime(2026, 10, 8, 12, 0, 0)
AREA = AreaReference(station_id="STN-001", area_id="PA-001-P", kind=AreaKind.PLATFORM)
# The fake log never touches the session, so any object will do.
SESSION = cast(AsyncSession, object())

OVERDUE_AT = NOW - timedelta(minutes=5)
CLEARED_AT = NOW - timedelta(minutes=1)
OPEN_EPISODE = OverdueEpisode(overdue_at=OVERDUE_AT, cleared_at=None)
CLEARED_EPISODE = OverdueEpisode(overdue_at=OVERDUE_AT, cleared_at=CLEARED_AT)


# Stands in for the overdue_log repository until its storage is decided (T6a).
class FakeOverdueLog:
    def __init__(self) -> None:
        self.entries: list[OverdueDetected | OverdueCleared] = []
        self.append_calls = 0

    async def get_entry_ids(self, session: AsyncSession) -> set[str]:
        return {entry.stable_entry_id for entry in self.entries}

    async def append_entries(
        self,
        session: AsyncSession,
        entries: list[OverdueDetected | OverdueCleared],
    ) -> None:
        self.append_calls += 1
        self.entries.extend(entries)


@pytest.fixture
def log(monkeypatch) -> FakeOverdueLog:
    fake = FakeOverdueLog()
    monkeypatch.setattr(overdue_tracker, "get_entry_ids", fake.get_entry_ids)
    monkeypatch.setattr(overdue_tracker, "append_entries", fake.append_entries)
    return fake


def stations_with(*episodes: OverdueEpisode) -> list[StationCoverageReport]:
    report = AreaCoverageReport(
        area=AREA,
        last_covered_at=NOW - timedelta(minutes=65),
        covered_now=False,
        shift_start_time=None,
        current_steward_ids=frozenset(),
        episodes=episodes,
        time_until_next_needed_patrol=timedelta(minutes=60),
        as_of=NOW,
    )
    return [StationCoverageReport(station_id="STN-001", areas=(report,))]


async def test_open_episode_is_logged_as_detected_at_its_deadline(log):
    await OverdueTracker().track(SESSION, stations_with(OPEN_EPISODE), NOW)

    assert log.entries == [
        OverdueDetected(
            area=AREA,
            overdue_at=OVERDUE_AT,
            detected_at=NOW,
            last_covered_at=NOW - timedelta(minutes=65),
            source="system",
        )
    ]


async def test_cleared_episode_is_logged_as_detected_then_cleared(log):
    await OverdueTracker().track(SESSION, stations_with(CLEARED_EPISODE), NOW)

    detected, cleared = log.entries
    assert isinstance(detected, OverdueDetected)
    assert cleared == OverdueCleared(
        area=AREA,
        overdue_at=OVERDUE_AT,
        cleared_at=CLEARED_AT,
        source="system",
    )


async def test_tracking_twice_writes_nothing_the_second_time(log):
    tracker = OverdueTracker()
    stations = stations_with(CLEARED_EPISODE)

    await tracker.track(SESSION, stations, NOW)
    await tracker.track(SESSION, stations, NOW + timedelta(seconds=5))

    assert log.append_calls == 1
    assert len(log.entries) == 2


async def test_episode_that_clears_later_only_adds_the_cleared_entry(log):
    tracker = OverdueTracker()

    await tracker.track(SESSION, stations_with(OPEN_EPISODE), NOW)
    await tracker.track(SESSION, stations_with(CLEARED_EPISODE), NOW)

    assert [type(entry) for entry in log.entries] == [OverdueDetected, OverdueCleared]


async def test_reports_without_episodes_write_nothing(log):
    await OverdueTracker().track(SESSION, stations_with(), NOW)

    assert log.append_calls == 0
