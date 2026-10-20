"""
Repository of functions used to query the database related to the overdue log.
Append-only. The storage schema is open until the ADR-0008 decision.
"""

from uuid import UUID

from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.coverage import OverdueCleared, OverdueDetected


async def get_entry_ids(session: AsyncSession) -> set[UUID]:
    """The ids of every overdue entry already in the log.

    The tracker uses them to skip entries it wrote before, which is what makes
    tracking safe to repeat.
    """
    raise NotImplementedError


async def append_entries(
    session: AsyncSession,
    entries: list[OverdueDetected | OverdueCleared],
) -> None:
    """Add new entries to the overdue log.

    Inserts the entries and commits. There is no code path that updates or
    deletes a row, because the log is evidence of what the system detected and
    when.
    """
    raise NotImplementedError
