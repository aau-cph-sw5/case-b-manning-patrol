from datetime import datetime

from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.coverage import StationCoverage


# Command: appends what the system detected about overdue areas to the overdue
# log. Never edits an entry.
class OverdueTracker:
    async def track(
        self,
        session: AsyncSession,
        stations: list[StationCoverage],
        now: datetime,
    ) -> None:
        """Record in the overdue log what the system has detected.

        For each overdue episode of each area:
        - if no OverdueDetected for it is logged yet, append one with
          detected_at = now;
        - if the episode has a cleared_at and no OverdueCleared is logged yet,
          append one.

        Ids already in the log (get_entry_ids) are skipped, so calling this
        twice writes nothing the second time. An area without a deadline (never
        patrolled, no baseline) has no episode, so nothing is logged for it.
        Append-only: never updates or deletes.
        """
        raise NotImplementedError
