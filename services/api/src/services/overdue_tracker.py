# OverdueTracker: appends the overdue episodes found in the coverage reports to
# the overdue log, skipping entries it already wrote. Never edits an entry.

from datetime import datetime

from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.repository.overdue_log import append_entries, get_entry_ids
from src.models.coverage import (
    AreaCoverageReport,
    OverdueCleared,
    OverdueDetected,
    OverdueEpisode,
    StationCoverageReport,
)

OverdueEntry = OverdueDetected | OverdueCleared

SYSTEM_SOURCE = "system"


class OverdueTracker:
    async def track(
        self,
        session: AsyncSession,
        stations: list[StationCoverageReport],
        now: datetime,
    ) -> None:
        entries = self._entries_for_stations(stations, now)
        if not entries:
            return

        new_entries = self._not_yet_logged(entries, await get_entry_ids(session))
        if new_entries:
            await append_entries(session, new_entries)

    def _entries_for_stations(
        self,
        stations: list[StationCoverageReport],
        now: datetime,
    ) -> list[OverdueEntry]:
        entries: list[OverdueEntry] = []
        for station in stations:
            for area_report in station.areas:
                for episode in area_report.episodes:
                    entries.extend(self._entries_for_episode(area_report, episode, now))
        return entries

    @staticmethod
    def _entries_for_episode(
        area_report: AreaCoverageReport,
        episode: OverdueEpisode,
        now: datetime,
    ) -> list[OverdueEntry]:
        detected = OverdueDetected(
            area=area_report.area,
            overdue_at=episode.overdue_at,
            detected_at=now,
            last_covered_at=area_report.last_covered_at,
            source=SYSTEM_SOURCE,
        )
        if episode.cleared_at is None:
            return [detected]

        cleared = OverdueCleared(
            area=area_report.area,
            overdue_at=episode.overdue_at,
            cleared_at=episode.cleared_at,
            source=SYSTEM_SOURCE,
        )
        return [detected, cleared]

    @staticmethod
    def _not_yet_logged(
        entries: list[OverdueEntry],
        logged_ids: set[str],
    ) -> list[OverdueEntry]:
        known_ids = set(logged_ids)
        new_entries: list[OverdueEntry] = []
        for entry in entries:
            if entry.stable_entry_id not in known_ids:
                known_ids.add(entry.stable_entry_id)
                new_entries.append(entry)
        return new_entries
