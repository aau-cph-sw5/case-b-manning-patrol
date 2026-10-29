import asyncio
from collections.abc import Callable
from datetime import datetime

from sqlmodel.ext.asyncio.session import AsyncSession

from src.services.station_coverage.shift_schedule import ShiftSchedule
from src.services.train_manning.train_manning_publisher import (
    TrainManningPublisher,
)
from src.services.train_manning.train_manning_service import (
    TrainManningService,
)


class TrainManningUpdater:
    def __init__(
        self,
        service: TrainManningService,
        publisher: TrainManningPublisher,
        session_factory: Callable[[], AsyncSession],
        clock: Callable[[], datetime],
        shift_schedule: ShiftSchedule,
    ) -> None:
        self._service = service
        self._publisher = publisher
        self._session_factory = session_factory
        self._clock = clock
        self._shift_schedule = shift_schedule
        self._lock = asyncio.Lock()
        self._last_published: list[TrainManningReport] = []

    async def refresh(self) -> None:
        async with self._lock:
            now = self._clock()
            shift = self._shift_schedule.latest_shift(now)
            as_of = min(now, shift.end)
            async with self._session_factory() as session:
                reports = await self._service.compute_manning_reports(
                    session, as_of, shift_start_time=shift.start
                )
            self._last_published = reports
            self._publisher.publish(reports)

    def snapshot(self) -> list[TrainManningReport]:
        return list(self._last_published)
