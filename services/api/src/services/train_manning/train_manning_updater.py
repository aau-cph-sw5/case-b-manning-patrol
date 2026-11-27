"""Recompute and publish train manning in one serialized step."""

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime

from sqlmodel.ext.asyncio.session import AsyncSession

from src.domain.train_manning import TrainManningReport
from src.services.shared.shift_schedule import ShiftSchedule
from src.services.train_manning.train_manning_publisher import TrainManningPublisher
from src.services.train_manning.train_manning_service import TrainManningService


@dataclass
class TrainManningDeps:
    """Database sessions, clock and shift schedule used by the updater."""

    session_factory: Callable[[], AsyncSession]
    clock: Callable[[], datetime]
    shift_schedule: ShiftSchedule


@dataclass
class TrainManningUpdater:
    """Keep the latest train manning reports current and push them to the publisher.

    Called both by the clock tick and after new events are ingested.
    """

    service: TrainManningService
    publisher: TrainManningPublisher
    deps: TrainManningDeps
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    _last_published: list[TrainManningReport] = field(default_factory=list)

    async def refresh(self) -> None:
        """Recompute manning for the current shift and publish it.

        Uses the latest shift from the schedule and computes manning as of the
        earlier of the clock time and the shift end, so a finished shift stays
        frozen at its end. Calls are serialized: a second call waits for the
        first to finish. The reports are stored for ``snapshot`` before they
        are published.
        """
        async with self._lock:
            now = self.deps.clock()
            shift = self.deps.shift_schedule.latest_shift(now)
            as_of = min(now, shift.end)
            async with self.deps.session_factory() as session:
                reports = await self.service.compute_manning_reports(
                    session, as_of, shift_start_time=shift.start
                )
            self._last_published = reports
            self.publisher.publish(reports)

    def snapshot(self) -> list[TrainManningReport]:
        """Return a copy of the last published reports, empty before any refresh."""
        return list(self._last_published)
