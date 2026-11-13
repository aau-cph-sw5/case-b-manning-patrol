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

    async def get_entry_ids(self, session: AsyncSession) -> set[str]:
        return {entry.stable_entry_id for entry in self.entries}

    async def append_entries(
        self, session: AsyncSession, entries: list[AtRiskDetected]
    ) -> None:
        self.entries.extend(entries)


@pytest.fixture(autouse=True)
def log(monkeypatch) -> FakeAtRiskLog:
    fake = FakeAtRiskLog()
    monkeypatch.setattr(at_risk_tracker, "get_entry_ids", fake.get_entry_ids)
    monkeypatch.setattr(at_risk_tracker, "append_entries", fake.append_entries)
    return fake


async def test_area_counts_once_when_it_crosses_the_threshold(station_report, now, log):
    tracker = AtRiskTracker()
    report = station_report(
        "marmorkirken", covered_now=False, as_of=now, last_covered_at=now
    )

    assert (
        await tracker.track(
            SESSION, [report], now + timedelta(minutes=44), THRESHOLD, shift_start=now
        )
        == 0
    )
    assert (
        await tracker.track(
            SESSION, [report], now + timedelta(minutes=45), THRESHOLD, shift_start=now
        )
        == 1
    )
    assert (
        await tracker.track(
            SESSION, [report], now + timedelta(minutes=50), THRESHOLD, shift_start=now
        )
        == 0
    )
    assert len(log.entries) == 1


async def test_covered_area_is_never_counted(station_report, now, log):
    tracker = AtRiskTracker()
    report = station_report(
        "kongens-nytorv", covered_now=True, as_of=now, last_covered_at=None
    )

    assert (
        await tracker.track(
            SESSION, [report], now + timedelta(hours=3), THRESHOLD, shift_start=now
        )
        == 0
    )
    assert log.entries == []


async def test_rescued_area_counts_again_in_a_new_episode(station_report, now, log):
    tracker = AtRiskTracker()

    first = station_report(
        "marmorkirken", covered_now=False, as_of=now, last_covered_at=now
    )
    assert (
        await tracker.track(
            SESSION, [first], now + timedelta(minutes=45), THRESHOLD, shift_start=now
        )
        == 1
    )

    rescued_at = now + timedelta(minutes=50)
    second = station_report(
        "marmorkirken", covered_now=False, as_of=rescued_at, last_covered_at=rescued_at
    )
    assert (
        await tracker.track(
            SESSION,
            [second],
            rescued_at + timedelta(minutes=44),
            THRESHOLD,
            shift_start=now,
        )
        == 0
    )
    assert (
        await tracker.track(
            SESSION,
            [second],
            rescued_at + timedelta(minutes=45),
            THRESHOLD,
            shift_start=now,
        )
        == 1
    )
    assert len(log.entries) == 2


async def test_entries_are_stamped_with_the_given_shift_start(station_report, now, log):
    tracker = AtRiskTracker()
    report = station_report(
        "marmorkirken", covered_now=False, as_of=now, last_covered_at=now
    )
    shift_start = now - timedelta(hours=8)

    assert (
        await tracker.track(
            SESSION,
            [report],
            now + timedelta(minutes=45),
            THRESHOLD,
            shift_start=shift_start,
        )
        == 1
    )

    assert log.entries[0].shift_start == shift_start


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
        await tracker.track(
            SESSION, reports, now + timedelta(minutes=45), THRESHOLD, shift_start=now
        )
        == 2
    )
    assert (
        await tracker.track(
            SESSION, reports, now + timedelta(minutes=46), THRESHOLD, shift_start=now
        )
        == 0
    )

    assert {entry.area.station_id for entry in log.entries} == {
        "marmorkirken",
        "kongens-nytorv",
    }
