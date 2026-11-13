"""Queries for the append-only at-risk log."""

from datetime import datetime

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models.at_risk_log import AtRiskLogEntry
from src.domain.coverage import AtRiskDetected


async def append_new_entries(
    session: AsyncSession, entries: list[AtRiskDetected]
) -> int:
    """Insert entries not logged yet and commit. Return how many were added."""
    if not entries:
        return 0
    result = await session.exec(select(AtRiskLogEntry.entry_id))
    in_database_ids = set(result.all())
    new_ids = [
        entry for entry in entries if entry.stable_entry_id not in in_database_ids
    ]
    if new_ids:
        session.add_all([_to_row(entry) for entry in new_ids])
        await session.commit()
    return len(new_ids)


async def count_episodes(session: AsyncSession, shift_start: datetime) -> int:
    """Return how many at-risk episodes were logged for the given shift."""
    result = await session.exec(
        select(AtRiskLogEntry).where(AtRiskLogEntry.shift_start == shift_start)
    )
    return len(result.all())


def _to_row(entry: AtRiskDetected) -> AtRiskLogEntry:
    return AtRiskLogEntry(
        entry_id=entry.stable_entry_id,
        station_id=entry.area.station_id,
        area_id=entry.area.area_id,
        area_kind=entry.area.kind,
        at_risk_at=entry.at_risk_at,
        overdue_at=entry.overdue_at,
        detected_at=entry.detected_at,
        shift_start=entry.shift_start,
        source=entry.source,
    )
