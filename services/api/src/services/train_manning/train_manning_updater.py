import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime

from sqlmodel.ext.asyncio.session import AsyncSession

from src.domain.train_manning import TrainManningReport
from src.services.station_coverage.shift_schedule import ShiftSchedule
from src.services.train_manning.train_manning_publisher import (
    TrainManningPublisher,
)
from src.services.train_manning.train_manning_service import (
    TrainManningService,
)


@dataclass
class TrainManningDeps:
    session_factory: Callable[[], AsyncSession]
    clock: Callable[[], datetime]
    shift_schedule: ShiftSchedule


@dataclass
class TrainManningUpdater:
    service: TrainManningService
    publisher: TrainManningPublisher
    deps: TrainManningDeps
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    _last_published: list[TrainManningReport] = field(default_factory=list)

    async def refresh(self) -> None:
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
        return list(self._last_published)
