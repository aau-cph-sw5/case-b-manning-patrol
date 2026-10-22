import asyncio
import contextlib
import datetime
from datetime import timedelta

from src.services.coverage.coverage_updater import ClockTick, CoverageUpdater


class FakeSession:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        return None

    async def commit(self):
        pass


class FakeService:
    def __init__(self):
        self.reports = []

    async def compute_coverage_reports(self, session, now, baseline=None):
        return self.reports


class FakeTracker:
    def __init__(self, events):
        self.events = events

    async def track(self, session, stations, now):
        self.events.append("track")


class FakePublisher:
    def __init__(self, events):
        self.events = events
        self.publishes = []

    def publish(self, coverage):
        self.events.append("publish")
        self.publishes.append([report.station_id for report in coverage])


class FakeClock:
    def __init__(self, times):
        self._times = iter(times)

    def __call__(self):
        return next(self._times)


def make_updater(clock_times):
    events = []
    service = FakeService()
    tracker = FakeTracker(events)
    publisher = FakePublisher(events)
    return (
        CoverageUpdater(
            service=service,  # ty: ignore[invalid-argument-type]
            tracker=tracker,  # ty: ignore[invalid-argument-type]
            publisher=publisher,
            session_factory=lambda: FakeSession(),  # ty: ignore[invalid-argument-type]
            clock=FakeClock(clock_times),
        ),
        service,
        publisher,
        events,
    )


async def test_first_refresh_publishes_every_station(station_report, now):
    updater, service, publisher, _ = make_updater([now])
    service.reports = [
        station_report(
            "marmorkirken", covered_now=True, as_of=now, last_covered_at=now
        ),
        station_report(
            "kongens-nytorv", covered_now=False, as_of=now, last_covered_at=None
        ),
    ]

    await updater.refresh()

    assert publisher.publishes == [["marmorkirken", "kongens-nytorv"]]


async def test_refresh_publishes_only_the_stations_that_changed(station_report):
    first_now = datetime.datetime(2026, 10, 19, 1, 0)
    second_now = first_now + timedelta(minutes=30)
    updater, service, publisher, _ = make_updater([first_now, second_now])
    service.reports = [
        station_report(
            "marmorkirken",
            covered_now=True,
            as_of=first_now,
            last_covered_at=first_now,
        ),
        station_report(
            "kongens-nytorv",
            covered_now=True,
            as_of=first_now,
            last_covered_at=first_now,
        ),
    ]
    await updater.refresh()

    service.reports = [
        # marmorkirken: steward left.
        station_report(
            "marmorkirken",
            covered_now=False,
            as_of=second_now,
            last_covered_at=first_now,
        ),
        # kongens-nytorv: only as_of moved.
        station_report(
            "kongens-nytorv",
            covered_now=True,
            as_of=second_now,
            last_covered_at=first_now,
        ),
    ]
    await updater.refresh()

    assert publisher.publishes[-1] == ["marmorkirken"]


async def test_unchanged_refresh_publishes_nothing(station_report):
    first_now = datetime.datetime(2026, 10, 19, 1, 0)
    second_now = first_now + timedelta(seconds=5)
    updater, service, publisher, _ = make_updater([first_now, second_now])
    service.reports = [
        station_report(
            "marmorkirken",
            covered_now=True,
            as_of=first_now,
            last_covered_at=first_now,
        )
    ]
    await updater.refresh()

    service.reports = [
        station_report(
            "marmorkirken",
            covered_now=True,
            as_of=second_now,
            last_covered_at=first_now,
        )
    ]
    await updater.refresh()

    assert publisher.publishes == [["marmorkirken"]]


async def test_tracker_logs_before_publisher_pushes(station_report, now):
    updater, service, publisher, events = make_updater([now])
    service.reports = [
        station_report("marmorkirken", covered_now=True, as_of=now, last_covered_at=now)
    ]

    await updater.refresh()

    assert events == ["track", "publish"]


async def test_snapshot_returns_latest_state_of_every_station(station_report):
    first_now = datetime.datetime(2026, 10, 19, 1, 0)
    second_now = first_now + timedelta(minutes=30)
    updater, service, publisher, _ = make_updater([first_now, second_now])
    service.reports = [
        station_report(
            "marmorkirken",
            covered_now=True,
            as_of=first_now,
            last_covered_at=first_now,
        )
    ]
    await updater.refresh()

    service.reports = [
        station_report(
            "marmorkirken",
            covered_now=False,
            as_of=second_now,
            last_covered_at=first_now,
        )
    ]
    await updater.refresh()

    snapshot = {report.station_id: report for report in updater.snapshot()}
    assert snapshot["marmorkirken"].areas[0].covered_now is False


async def test_snapshot_keeps_stations_that_were_not_republished(station_report):
    first_now = datetime.datetime(2026, 10, 19, 1, 0)
    second_now = first_now + timedelta(minutes=30)
    updater, service, _, _ = make_updater([first_now, second_now])
    unchanged = station_report(
        "kongens-nytorv", covered_now=True, as_of=first_now, last_covered_at=first_now
    )
    service.reports = [
        station_report(
            "marmorkirken",
            covered_now=True,
            as_of=first_now,
            last_covered_at=first_now,
        ),
        unchanged,
    ]
    await updater.refresh()

    service.reports = [
        station_report(
            "marmorkirken",
            covered_now=False,
            as_of=second_now,
            last_covered_at=first_now,
        ),
        unchanged,
    ]
    await updater.refresh()

    assert [report.station_id for report in updater.snapshot()] == [
        "marmorkirken",
        "kongens-nytorv",
    ]


async def test_clock_tick_refreshes_until_cancelled():
    class FakeTickUpdater:
        def __init__(self):
            self.refreshes = 0

        async def refresh(self):
            self.refreshes += 1

    fake_updater = FakeTickUpdater()
    tick = ClockTick(
        fake_updater,  # ty: ignore[invalid-argument-type]
        interval=timedelta(milliseconds=10),
    )
    task = asyncio.create_task(tick.run())
    try:
        await asyncio.sleep(0.05)
    finally:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

    assert fake_updater.refreshes >= 2
