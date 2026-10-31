"""Recompute, log and publish station coverage in one serialized step."""

import asyncio
import logging
from collections.abc import Callable
from datetime import datetime

from sqlmodel.ext.asyncio.session import AsyncSession

from src.domain.coverage import StationCoverageReport
from src.services.station_coverage.coverage_publisher import CoveragePublisher
from src.services.station_coverage.coverage_service import CoverageService
from src.services.station_coverage.overdue_tracker import OverdueTracker
from src.services.station_coverage.shift_schedule import ShiftSchedule

logger = logging.getLogger(__name__)


class CoverageUpdater:
    """Keep the latest coverage reports current and push them to the publisher.

    Called both by the clock tick and after new events are ingested.
    """

    def __init__(
        self,
        service: CoverageService,
        tracker: OverdueTracker,
        publisher: CoveragePublisher,
        session_factory: Callable[[], AsyncSession],
        clock: Callable[[], datetime],
        shift_schedule: ShiftSchedule,
    ) -> None:
        self._service = service
        self._tracker = tracker
        self._publisher = publisher
        self._session_factory = session_factory
        self._clock = clock
        self._shift_schedule = shift_schedule
        self._lock = asyncio.Lock()
        self._last_published: list[StationCoverageReport] = []

    async def refresh(self) -> None:
        """Recompute coverage for the current shift, log overdue changes, publish.

        Uses the latest shift from the schedule and computes coverage as of
        the earlier of the clock time and the shift end, so a finished shift
        stays frozen at its end. Overdue episodes are written to the overdue
        log with the actual clock time as detection time, and the session is
        committed before the reports are stored for ``snapshot`` and
        published. Concurrent calls are serialized by a lock.
        """
        async with self._lock:
            now = self._clock()
            shift = self._shift_schedule.latest_shift(now)
            as_of = min(now, shift.end)
            async with self._session_factory() as session:
                reports = await self._service.compute_coverage_reports(
                    session, as_of, shift_start_time=shift.start
                )
                await self._tracker.track(session, reports, now)
                await session.commit()
            self._last_published = reports
            self._publisher.publish(reports)

    def snapshot(self) -> list[StationCoverageReport]:
        """Return a copy of the last published reports, empty before any refresh."""
        return list(self._last_published)
