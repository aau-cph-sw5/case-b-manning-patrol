"""
Repository of functions used to query the database
"""

from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models import PatrolArea, Station


async def get_patrol_area(session: AsyncSession, beacon_id: UUID) -> PatrolArea:
    result = await session.exec(
        select(PatrolArea).where(PatrolArea.beacon_id == beacon_id)
    )

    return result.one()


async def get_patrol_areas(session: AsyncSession) -> list[PatrolArea]:
    result = await session.exec(select(PatrolArea))

    return list(result.all())


async def get_station(session: AsyncSession, id: str) -> Station:
    result = await session.exec(select(Station).where(Station.id == id))
    return result.one()


async def get_stations(session: AsyncSession) -> list[Station]:
    result = await session.exec(select(Station))
    return list(result.all())
