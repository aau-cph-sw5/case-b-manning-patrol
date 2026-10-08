"""
Repository of functions used to query the database related to Events
"""

from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.event import Event


async def get_event(session: AsyncSession, event_id: UUID) -> Event:
    result = await session.exec(select(Event).where(Event.event_id == event_id))

    return result.one()


async def get_patrol_areas(session: AsyncSession) -> list[Event]:
    result = await session.exec(select(Event))

    return list(result.all())
