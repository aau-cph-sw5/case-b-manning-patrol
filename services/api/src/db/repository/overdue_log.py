"""Queries for the append-only overdue log."""

from datetime import datetime, timedelta

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models.overdue_log import OverdueLogEntry
from src.domain.coverage import OverdueCleared, OverdueDetected


async def get_entry_ids(session: AsyncSession) -> set[str]:
    """Return the IDs of all logged entries."""
    result = await session.exec(select(OverdueLogEntry.entry_id))
    return set(result.all())


async def append_entries(
    session: AsyncSession,
    entries: list[OverdueDetected | OverdueCleared],
) -> None:
    """Insert and commit the entries."""
    session.add_all([_to_row(entry) for entry in entries])
    await session.commit()


async def overdue_onsets(
    session: AsyncSession, start: datetime, end: datetime
) -> list[timedelta]:
    """Return how far into the shift each overdue episode began.

    The onset is ``overdue_at - start`` for every DETECTED episode whose
    ``overdue_at`` falls in ``[start, end)``; every episode has a DETECTED
    row whether it is still open or already cleared.
    """
    result = await session.exec(
        select(OverdueLogEntry).where(
            OverdueLogEntry.entry_type == "DETECTED",
            OverdueLogEntry.overdue_at >= start,
            OverdueLogEntry.overdue_at < end,
        )
    )
    return [row.overdue_at - start for row in result.all()]


def _to_row(entry: OverdueDetected | OverdueCleared) -> OverdueLogEntry:
    if isinstance(entry, OverdueDetected):
        return OverdueLogEntry(
            entry_id=entry.stable_entry_id,
            entry_type="DETECTED",
            station_id=entry.area.station_id,
            area_id=entry.area.area_id,
            area_kind=entry.area.kind,
            overdue_at=entry.overdue_at,
            detected_at=entry.detected_at,
            last_covered_at=entry.last_covered_at,
            cleared_at=None,
            source=entry.source,
        )
    return OverdueLogEntry(
        entry_id=entry.stable_entry_id,
        entry_type="CLEARED",
        station_id=entry.area.station_id,
        area_id=entry.area.area_id,
        area_kind=entry.area.kind,
        overdue_at=entry.overdue_at,
        detected_at=None,
        last_covered_at=None,
        cleared_at=entry.cleared_at,
        source=entry.source,
    )
