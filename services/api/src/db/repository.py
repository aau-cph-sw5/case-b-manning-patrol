"""
Repository of functions used to query the database
"""

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession


async def fetch_events(session: AsyncSession):
    statement = select(Event)  # Model is probably called something else
    events = await session.exec(statement)

    return events.all()


async def fetch_event(session: AsyncSession, event_id: str):
    statement = select(Event).where(
        Event.id == event.id
    )  # Might not event id as PK and might not be str
    event = await session.exec(statement)
    return event.one_or_none()
