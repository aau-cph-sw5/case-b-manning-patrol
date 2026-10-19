from datetime import datetime

from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.repository.overdue_log import append_entries, get_entry_ids
from src.models.coverage import (
    OverdueCleared,
    OverdueDetected,
    StationCoverageReport,
)


# Command: appends what the system detected about overdue areas to the overdue
# log. Never edits an entry.
class OverdueTracker:
    async def track(
        self,
        session: AsyncSession,
        stations: list[StationCoverageReport],
        now: datetime,
    ) -> None:
        pending: list[OverdueDetected | OverdueCleared] = []
        for station in stations:
            for area_report in station.areas:
                for episode in area_report.episodes:
                    pending.append(
                        OverdueDetected(
                            area=area_report.area,
                            overdue_at=episode.overdue_at,
                            detected_at=now,
                            last_covered_at=area_report.last_covered_at,
                            source="system",
                        )
                    )
                    if episode.cleared_at is not None:
                        pending.append(
                            OverdueCleared(
                                area=area_report.area,
                                overdue_at=episode.overdue_at,
                                cleared_at=episode.cleared_at,
                                source="system",
                            )
                        )

        if not pending:
            return

        existing_ids = await get_entry_ids(session)
        new_entries: list[OverdueDetected | OverdueCleared] = []
        seen: set[str] = set()
        for entry in pending:
            entry_id: str = entry.stable_entry_id
            if entry_id not in seen and entry_id not in existing_ids:
                seen.add(entry_id)
                new_entries.append(entry)

        if new_entries:
            await append_entries(session, new_entries)
