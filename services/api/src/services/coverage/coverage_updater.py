import asyncio
from collections.abc import Callable
from datetime import datetime, timedelta

from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.coverage import StationCoverageReport
from src.services.coverage.coverage_publisher import CoveragePublisher
from src.services.coverage.coverage_service import CoverageService
from src.services.overdue_tracker import OverdueTracker


class CoverageUpdater:
    def __init__(
        self,
        service: CoverageService,
        tracker: OverdueTracker,
        publisher: CoveragePublisher,
        session_factory: Callable[[], AsyncSession],
        clock: Callable[[], datetime],
    ) -> None:
        self._service = service
        self._tracker = tracker
        self._publisher = publisher
        self._session_factory = session_factory
        self._clock = clock
        self._lock = asyncio.Lock()
        self._last_published: list[StationCoverageReport] = []

    async def refresh(self) -> None:
        async with self._lock:
            now = self._clock()
            async with self._session_factory() as session:
                reports = await self._service.compute_coverage_reports(session, now)
                await self._tracker.track(session, reports, now)
                await session.commit()
            self._last_published = reports
            self._publisher.publish(reports)

    def snapshot(self) -> list[StationCoverageReport]:
        return list(self._last_published)


class ClockTick:
    def __init__(self, updater: CoverageUpdater, interval: timedelta) -> None:
        self._updater = updater
        self._interval = interval

    async def run(self) -> None:
        while True:
            await self._updater.refresh()
            await asyncio.sleep(self._interval.total_seconds())
