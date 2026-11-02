"""Count at-risk episodes and append them to the at-risk log."""

from datetime import datetime, timedelta

from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.repository.at_risk_log import append_new_entries
from src.domain.coverage import AtRiskDetected, StationCoverageReport

SYSTEM_SOURCE = "system"


class AtRiskTracker:
    """Counts how many new at-risk episodes have been observed in a shift."""

    def __init__(self) -> None:
        # (station_id, area_id, overdue_at)
        # overdue_at makes the key unique pr. episode.
        self._counted: set[tuple[str, str, datetime]] = set()
        self.total: int = 0
        self.shift_start: datetime | None = None

    async def track(
        self,
        session: AsyncSession,
        reports: list[StationCoverageReport],
        now: datetime,
        threshold: timedelta,
    ) -> int:
        """Count new at-risk episodes and append them to the at-risk log."""
        entries = self._new_entries(reports, now, threshold)
        if entries:
            await append_new_entries(session, entries)
        return len(entries)

    def _new_entries(
        self,
        reports: list[StationCoverageReport],
        now: datetime,
        threshold: timedelta,
    ) -> list[AtRiskDetected]:
        """Return the episodes in these reports that were not counted yet."""
        new_entries: list[AtRiskDetected] = []
        for station in reports:
            for area in station.areas:
                if area.covered_now or area.overdue_at is None:
                    continue
                at_risk_at = area.overdue_at - threshold
                key = (station.station_id, area.area.area_id, area.overdue_at)
                if now >= at_risk_at and key not in self._counted:
                    self._counted.add(key)
                    new_entries.append(
                        AtRiskDetected(
                            area=area.area,
                            at_risk_at=at_risk_at,
                            overdue_at=area.overdue_at,
                            detected_at=now,
                            shift_start=self.shift_start or now,
                            source=SYSTEM_SOURCE,
                        )
                    )
        self.total += len(new_entries)
        return new_entries

    def observe(
        self,
        reports: list[StationCoverageReport],
        now: datetime,
        threshold: timedelta,
    ) -> int:
        """Return the number of new at-risk episodes found in this calculation."""
        return len(self._new_entries(reports, now, threshold))

    def reset_for_new_shift(self, shift_start: datetime) -> None:
        """Called when the shift changes, so the shift starts from zero."""
        self._counted.clear()
        self.total = 0
        self.shift_start = shift_start
