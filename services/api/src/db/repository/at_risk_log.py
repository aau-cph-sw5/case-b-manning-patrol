"""Queries for the append-only at-risk log."""

from datetime import datetime

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models.at_risk_log import AtRiskLogEntry
from src.domain.coverage import AtRiskDetected


async def get_entry_ids(session: AsyncSession) -> set[str]:
    """Return the IDs of all logged entries."""
    result = await session.exec(select(AtRiskLogEntry.entry_id))
    return set(result.all())


async def append_entries(session: AsyncSession, entries: list[AtRiskDetected]) -> None:
    """Insert and commit the entries."""
    session.add_all([_to_row(entry) for entry in entries])
    await session.commit()


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
