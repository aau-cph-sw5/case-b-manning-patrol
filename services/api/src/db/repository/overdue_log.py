
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.coverage import OverdueCleared, OverdueDetected
from src.models.overdue_log import OverdueLogEntry


async def get_entry_ids(session: AsyncSession) -> set[str]:
    result = await session.exec(select(OverdueLogEntry.entry_id))
    return set(result.all())


async def append_entries(
    session: AsyncSession,
    entries: list[OverdueDetected | OverdueCleared],
) -> None:
    session.add_all([_to_row(entry) for entry in entries])
    await session.commit()


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
