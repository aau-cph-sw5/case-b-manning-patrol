"""
Repository of functions used to query the database related to Station
"""

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models import Station


async def get_station(session: AsyncSession, id: str) -> Station:
    result = await session.exec(select(Station).where(Station.id == id))
    return result.one()


async def get_stations(session: AsyncSession) -> list[Station]:
    result = await session.exec(select(Station))
    return list(result.all())
