"""Rebuild the compliance picture of a past shift from the stored record."""

from dataclasses import dataclass
from datetime import date, datetime

from sqlmodel.ext.asyncio.session import AsyncSession

from src.domain.compliance import CompliancePicture
from src.services.shared.shift_schedule import ShiftSchedule
from src.services.station_coverage.coverage_service import CoverageService
from src.services.train_manning.train_manning_service import TrainManningService


@dataclass
class ComplianceReconstructor:
    """Reproduce station coverage and train manning for the shift on a date.

    Uses the same services as the live dashboard, so a reconstructed picture
    is computed exactly like the one shown at the time.
    """

    coverage_service: CoverageService
    manning_service: TrainManningService
    shift_schedule: ShiftSchedule

    async def reconstruct(
        self,
        session: AsyncSession,
        day: date,
        current_time: datetime,
        known_at: datetime | None = None,
    ) -> CompliancePicture:
        """Return the compliance picture of the shift that starts on ``day``.

        Events are placed in the shift by their device timestamp. With
        ``known_at``, only events the backend had received by then count, and
        the shift is evaluated no later than ``known_at``, so the result
        matches what the live dashboard showed at that moment. Without it,
        every stored event is used, including ones that arrived late.

        ``current_time`` is passed in instead of read from the clock so
        results are deterministic; a shift still running at that time is
        evaluated up to it. Both datetimes must be timezone-aware.

        Raises ValueError if the shift had not started by ``current_time`` or
        by ``known_at``, since there is nothing to reconstruct yet.
        """
        shift = self.shift_schedule.shift_on(day)
        as_of = min(shift.end, current_time)
        if known_at is not None:
            as_of = min(as_of, known_at)
        if as_of < shift.start:
            raise ValueError(f"The shift on {day} had not started by {as_of}")

        stations = await self.coverage_service.compute_coverage_reports(
            session,
            now=as_of,
            shift_start_time=shift.start,
            known_at=known_at,
        )
        trains = await self.manning_service.compute_manning_reports(
            session,
            now=as_of,
            shift_start_time=shift.start,
            known_at=known_at,
        )
        return CompliancePicture(
            shift=shift,
            as_of=as_of,
            known_at=known_at,
            stations=tuple(stations),
            trains=tuple(trains),
        )
