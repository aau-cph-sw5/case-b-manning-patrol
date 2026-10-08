"""
Repository of functions used to query the database related to PatrolArea
"""

from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models import PatrolArea


async def get_patrol_area(session: AsyncSession, beacon_id: UUID) -> PatrolArea:
    result = await session.exec(
        select(PatrolArea).where(PatrolArea.beacon_id == beacon_id)
    )

    return result.one()


async def get_patrol_areas(session: AsyncSession) -> list[PatrolArea]:
    result = await session.exec(select(PatrolArea))

    return list(result.all())
