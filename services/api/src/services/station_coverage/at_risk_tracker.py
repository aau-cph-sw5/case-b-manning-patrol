from datetime import datetime, timedelta

from src.domain.coverage import StationCoverageReport


class AtRiskTracker:
    """Counts how many new at-risk episodes have been observed in a shift."""

    def __init__(self) -> None:
        # (station_id, area_id, overdue_at)
        # overdue_at makes the key unique pr. episode.
        self._counted: set[tuple[str, str, datetime]] = set()
        self.total: int = 0
        self.shift_start: datetime | None = None

    def observe(
        self,
        reports: list[StationCoverageReport],
        now: datetime,
        threshold: timedelta,
    ) -> int:
        """Return the number of new at-risk episodes found in this calculation."""
        new = 0
        for station in reports:
            for area in station.areas:
                if area.covered_now or area.overdue_at is None:
                    continue
                at_risk_at = area.overdue_at - threshold
                key = (station.station_id, area.area.area_id, area.overdue_at)
                if now >= at_risk_at and key not in self._counted:
                    self._counted.add(key)
                    new += 1
        self.total += new
        return new

    def reset_for_new_shift(self, shift_start: datetime) -> None:
        """Called when the shift changes, so the shift starts from zero."""
        self._counted.clear()
        self.total = 0
        self.shift_start = shift_start
