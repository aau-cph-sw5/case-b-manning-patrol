import asyncio
from collections.abc import Callable
from datetime import datetime, timedelta

from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.coverage import StationCoverageReport
from src.services.coverage.coverage_publisher import CoveragePublisher
from src.services.coverage.coverage_service import CoverageService
from src.services.overdue_tracker import OverdueTracker


# Runs one coverage refresh: compute, log overdue, then publish the stations
# that changed. Called by ingestion and by ClockTick, one refresh at a time.
class CoverageUpdater:
    def __init__(
        self,
        service: CoverageService,
        tracker: OverdueTracker,
        publisher: CoveragePublisher,
        session_factory: Callable[[], AsyncSession],
        clock: Callable[[], datetime],
    ) -> None:
        """Hold everything one refresh needs.

        session_factory opens a fresh database session per refresh, because a
        refresh can run after the request that triggered it has closed its own
        session. clock returns the current time; passing it in lets tests
        control time. The lock makes sure only one refresh runs at a time, and
        last_published remembers the latest coverage of each station, so
        snapshot() can serve a dashboard that connects between refreshes.
        """
        self._service = service
        self._tracker = tracker
        self._publisher = publisher
        self._session_factory = session_factory
        self._clock = clock
        self._lock = asyncio.Lock()
        self._last_published: dict[str, StationCoverageReport] = {}

    async def refresh(self) -> None:
        """Bring the dashboards up to date with the latest coverage.

        Called after each new event (AC1) and on every clock tick.
        1. Take the lock, so two refreshes never run at once.
        2. Only then read the clock. Reading it before waiting for the lock
           could let an older now run after a newer one and publish an
           outdated state.
        3. Open a session, compute the coverage, then let the tracker log
           overdue changes and commit, so anything pushed as overdue is
           already durably in the log.
        4. With no await in between: find the stations whose state changed
           since the last refresh, remember the coverage of every station in
           last_published, and publish only the changed stations. Nothing is
           published when no station changed.
        """
        async with self._lock:
            now = self._clock()
            async with self._session_factory() as session:
                reports = await self._service.compute_coverage_reports(session, now)
                await self._tracker.track(session, reports, now)
                await session.commit()
            changed = self._changed(reports)
            self._last_published = {report.station_id: report for report in reports}
            if changed:
                self._publisher.publish(changed)

    def _changed(
        self, reports: list[StationCoverageReport]
    ) -> list[StationCoverageReport]:
        """The reports whose state differs from the last published one.

        A station that was never published counts as changed.
        """
        return [
            report
            for report in reports
            if report.station_id not in self._last_published
            or self._last_published[report.station_id].state() != report.state()
        ]

    def snapshot(self) -> list[StationCoverageReport]:
        """The coverage as last published, for a dashboard that just connected.

        Returns last_published as a list. Synchronous, so the stream route can
        subscribe and then take the snapshot without anything being published
        in between.
        """
        return list(self._last_published.values())


# Refreshes coverage on a timer, because window expiry and a threshold crossed
# mid-visit produce no event. Runs as the lifespan task started in main.py.
class ClockTick:
    def __init__(self, updater: CoverageUpdater, interval: timedelta) -> None:
        """Hold the updater and how often to refresh.

        interval is passed in, so tests can use a short one.
        """
        self._updater = updater
        self._interval = interval

    async def run(self) -> None:
        """Refresh coverage on a fixed interval until the app shuts down.

        Loop: call updater.refresh(), then sleep for interval. Needed because
        two things change coverage without any event arriving: a window running
        out, and an open visit crossing its threshold. Stops cleanly when the
        lifespan cancels the task.
        """
        while True:
            await self._updater.refresh()
            await asyncio.sleep(self._interval.total_seconds())
