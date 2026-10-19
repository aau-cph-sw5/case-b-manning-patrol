import asyncio
from collections.abc import Callable
from datetime import datetime, timedelta

from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.coverage import StationCoverageReport
from src.services.coverage.coverage_publisher import CoveragePublisher
from src.services.coverage.coverage_service import CoverageService
from src.services.overdue_tracker import OverdueTracker


# Runs one coverage refresh: compute, log overdue, then publish only stations
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
        last_published remembers what each station looked like when it was
        last pushed.
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
           overdue changes. Logging comes first, so anything pushed as overdue
           is already in the log.
        4. With no await in between: compare each station's state() with
           last_published, update last_published and publish only the stations
           that changed.
        """
        raise NotImplementedError

    def snapshot(self) -> list[StationCoverageReport]:
        """The coverage as last published, for a dashboard that just connected.

        Returns last_published as a list. Synchronous, so the stream route can
        subscribe and then take the snapshot without anything being published
        in between.
        """
        raise NotImplementedError


# Refreshes coverage on a timer, because window expiry and a threshold crossed
# mid-visit produce no event. Meant to run as a lifespan task (not wired yet).
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
        raise NotImplementedError
