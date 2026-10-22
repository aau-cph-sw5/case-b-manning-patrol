import asyncio
import contextlib
import datetime
import logging
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
        self.published = []

    def publish(self, coverage):
        self.events.append("publish")
        self.published.extend(coverage)


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


async def test_refresh_publishes_the_full_coverage_every_time(station_report):
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
    assert [report.station_id for report in publisher.published] == [
        "marmorkirken",
        "kongens-nytorv",
    ]

    publisher.published.clear()
    service.reports = [
        station_report(
            "marmorkirken",
            covered_now=False,
            as_of=second_now,
            last_covered_at=first_now,
        ),
        station_report(
            "kongens-nytorv",
            covered_now=True,
            as_of=second_now,
            last_covered_at=first_now,
        ),
    ]

    await updater.refresh()
    assert [report.station_id for report in publisher.published] == [
        "marmorkirken",
        "kongens-nytorv",
    ]


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


async def test_clock_tick_survives_a_failed_refresh():
    class FlakyThenSteadyUpdater:
        def __init__(self):
            self.refreshes = 0

        async def refresh(self):
            self.refreshes += 1
            if self.refreshes == 1:
                raise RuntimeError("database hiccup")

    fake_updater = FlakyThenSteadyUpdater()
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

    assert fake_updater.refreshes >= 3


async def test_clock_tick_logs_a_persistent_failure_once(caplog):
    caplog.set_level(logging.DEBUG)

    class AlwaysFailingUpdater:
        def __init__(self):
            self.refreshes = 0

        async def refresh(self):
            self.refreshes += 1
            raise RuntimeError("database down")

    fake_updater = AlwaysFailingUpdater()
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
    errors = [record for record in caplog.records if record.levelno >= logging.ERROR]
    assert len(errors) == 1


async def test_clock_tick_logs_recovery_once_and_resets_the_streak(caplog):
    caplog.set_level(logging.DEBUG)

    class FailsRecoversThenFailsAgainUpdater:
        def __init__(self):
            self.refreshes = 0

        async def refresh(self):
            self.refreshes += 1
            if self.refreshes == 1 or self.refreshes >= 4:
                raise RuntimeError("database hiccup")

    fake_updater = FailsRecoversThenFailsAgainUpdater()
    tick = ClockTick(
        fake_updater,  # ty: ignore[invalid-argument-type]
        interval=timedelta(milliseconds=10),
    )
    task = asyncio.create_task(tick.run())
    try:
        await asyncio.sleep(0.07)
    finally:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

    assert fake_updater.refreshes >= 4
    errors = [record for record in caplog.records if record.levelno >= logging.ERROR]
    assert len(errors) == 2
    recovery = [record for record in caplog.records if record.levelno == logging.INFO]
    assert len(recovery) == 1
    assert "recovered" in recovery[0].getMessage()
