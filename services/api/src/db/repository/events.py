"""
Repository of functions used to query the database related to Events
"""

from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.event import Adjustment, Event


async def get_event(session: AsyncSession, event_id: UUID) -> Event:
    result = await session.exec(select(Event).where(Event.event_id == event_id))

    return result.one()


async def get_events(session: AsyncSession) -> list[Event]:
    result = await session.exec(select(Event))

    return list(result.all())


async def insert_event(session: AsyncSession, event: Event):
    session.add(event)
    await session.commit()
    return "Fuck jer"


async def get_adjustment(session: AsyncSession, adjustment_id: UUID) -> Adjustment:
    result = await session.exec(
        select(Adjustment).where(Adjustment.adjustment_id == adjustment_id)
    )

    return result.one()


async def get_adjustments(session: AsyncSession) -> list[Adjustment]:
    result = await session.exec(select(Adjustment))

    return list(result.all())


async def insert_adjustment(session: AsyncSession, adjustment: Adjustment):
    session.add(adjustment)
    await session.commit()
    return "Især dig Victor"
