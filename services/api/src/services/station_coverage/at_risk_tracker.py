"""Count at-risk episodes and append them to the at-risk log."""

from datetime import datetime, timedelta

from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.repository.at_risk_log import append_entries, get_entry_ids
from src.domain.coverage import (
    AreaCoverageReport,
    AtRiskDetected,
    StationCoverageReport,
)

SYSTEM_SOURCE = "system"


class AtRiskTracker:
    """Record when areas reach the at-risk threshold."""

    async def track(
        self,
        session: AsyncSession,
        reports: list[StationCoverageReport],
        now: datetime,
        threshold: timedelta,
        shift_start: datetime,
    ) -> int:
        """Count new at-risk episodes and append them to the at-risk log."""
        entries = self._entries_for_reports(reports, now, threshold, shift_start)
        if not entries:
            return 0

        new_entries = self._not_yet_logged(entries, await get_entry_ids(session))
        if new_entries:
            await append_entries(session, new_entries)
        return len(new_entries)

    def _entries_for_reports(
        self,
        reports: list[StationCoverageReport],
        now: datetime,
        threshold: timedelta,
        shift_start: datetime,
    ) -> list[AtRiskDetected]:
        entries: list[AtRiskDetected] = []
        for station in reports:
            for area_report in station.areas:
                entry = self._entry_for_area(area_report, now, threshold, shift_start)
                if entry is not None:
                    entries.append(entry)
        return entries

    @staticmethod
    def _entry_for_area(
        area_report: AreaCoverageReport,
        now: datetime,
        threshold: timedelta,
        shift_start: datetime,
    ) -> AtRiskDetected | None:
        if area_report.covered_now or area_report.overdue_at is None:
            return None
        at_risk_at = area_report.overdue_at - threshold
        if now < at_risk_at:
            return None
        return AtRiskDetected(
            area=area_report.area,
            at_risk_at=at_risk_at,
            overdue_at=area_report.overdue_at,
            detected_at=now,
            shift_start=shift_start,
            source=SYSTEM_SOURCE,
        )

    @staticmethod
    def _not_yet_logged(
        entries: list[AtRiskDetected],
        logged_ids: set[str],
    ) -> list[AtRiskDetected]:
        known_ids = set(logged_ids)
        new_entries: list[AtRiskDetected] = []
        for entry in entries:
            if entry.stable_entry_id not in known_ids:
                known_ids.add(entry.stable_entry_id)
                new_entries.append(entry)
        return new_entries
