from datetime import timedelta
from typing import cast

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from src.domain.coverage import AtRiskDetected
from src.services.station_coverage import at_risk_tracker
from src.services.station_coverage.at_risk_tracker import AtRiskTracker

THRESHOLD = timedelta(minutes=15)

# The fake log never touches the session, so any object will do.
SESSION = cast(AsyncSession, object())


# Stands in for the at_risk_log repository in tests.
class FakeAtRiskLog:
    def __init__(self) -> None:
        self.entries: list[AtRiskDetected] = []

    async def append_new_entries(
        self, session: AsyncSession, entries: list[AtRiskDetected]
    ) -> int:
        self.entries.extend(entries)
        return len(entries)


@pytest.fixture(autouse=True)
def log(monkeypatch) -> FakeAtRiskLog:
    fake = FakeAtRiskLog()
    monkeypatch.setattr(at_risk_tracker, "append_new_entries", fake.append_new_entries)
    return fake


async def test_area_counts_once_when_it_crosses_the_threshold(station_report, now):
    tracker = AtRiskTracker()
    report = station_report(
        "marmorkirken", covered_now=False, as_of=now, last_covered_at=now
    )

    assert (
        await tracker.track(SESSION, [report], now + timedelta(minutes=44), THRESHOLD)
        == 0
    )
    assert (
        await tracker.track(SESSION, [report], now + timedelta(minutes=45), THRESHOLD)
        == 1
    )
    assert (
        await tracker.track(SESSION, [report], now + timedelta(minutes=50), THRESHOLD)
        == 0
    )
    assert tracker.total == 1


async def test_covered_area_is_never_counted(station_report, now):
    tracker = AtRiskTracker()
    report = station_report(
        "kongens-nytorv", covered_now=True, as_of=now, last_covered_at=None
    )

    assert (
        await tracker.track(SESSION, [report], now + timedelta(hours=3), THRESHOLD) == 0
    )
    assert tracker.total == 0


async def test_rescued_area_counts_again_in_a_new_episode(station_report, now):
    tracker = AtRiskTracker()

    first = station_report(
        "marmorkirken", covered_now=False, as_of=now, last_covered_at=now
    )
    assert (
        await tracker.track(SESSION, [first], now + timedelta(minutes=45), THRESHOLD)
        == 1
    )

    rescued_at = now + timedelta(minutes=50)
    second = station_report(
        "marmorkirken", covered_now=False, as_of=rescued_at, last_covered_at=rescued_at
    )
    assert (
        await tracker.track(
            SESSION, [second], rescued_at + timedelta(minutes=44), THRESHOLD
        )
        == 0
    )
    assert (
        await tracker.track(
            SESSION, [second], rescued_at + timedelta(minutes=45), THRESHOLD
        )
        == 1
    )
    assert tracker.total == 2


async def test_reset_for_new_shift_starts_from_zero(station_report, now):
    tracker = AtRiskTracker()
    report = station_report(
        "marmorkirken", covered_now=False, as_of=now, last_covered_at=now
    )
    await tracker.track(SESSION, [report], now + timedelta(minutes=45), THRESHOLD)

    tracker.reset_for_new_shift(now + timedelta(hours=8))

    assert tracker.total == 0
    assert tracker.shift_start == now + timedelta(hours=8)
    assert (
        await tracker.track(SESSION, [report], now + timedelta(minutes=45), THRESHOLD)
        == 1
    )


async def test_two_stations_count_independently(station_report, now, log):
    tracker = AtRiskTracker()
    reports = [
        station_report(
            "marmorkirken", covered_now=False, as_of=now, last_covered_at=now
        ),
        station_report(
            "kongens-nytorv", covered_now=False, as_of=now, last_covered_at=now
        ),
    ]

    assert (
        await tracker.track(SESSION, reports, now + timedelta(minutes=45), THRESHOLD)
        == 2
    )
    assert (
        await tracker.track(SESSION, reports, now + timedelta(minutes=46), THRESHOLD)
        == 0
    )

    assert {entry.area.station_id for entry in log.entries} == {
        "marmorkirken",
        "kongens-nytorv",
    }
    assert tracker.total == 2
