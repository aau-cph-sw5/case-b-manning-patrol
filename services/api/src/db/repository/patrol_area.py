"""Queries for patrol areas and their beacons."""

from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models import PatrolArea


async def get_patrol_area(session: AsyncSession, beacon_id: UUID) -> PatrolArea:
    """Return the patrol area for this beacon, or raise NoResultFound."""
    result = await session.exec(
        select(PatrolArea).where(PatrolArea.beacon_id == beacon_id)
    )

    return result.one()


async def get_patrol_areas(session: AsyncSession) -> list[PatrolArea]:
    """Return all patrol areas."""
    result = await session.exec(select(PatrolArea))

    return list(result.all())
