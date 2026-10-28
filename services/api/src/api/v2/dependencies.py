from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.main import engine
from src.services.event_producer import EventProducer


async def get_session() -> AsyncGenerator[AsyncSession]:
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


AsyncDbSessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_event_producer(session: AsyncDbSessionDep) -> EventProducer:
    return EventProducer(session, source="API")


EventProducerDep = Annotated[EventProducer, Depends(get_event_producer)]
