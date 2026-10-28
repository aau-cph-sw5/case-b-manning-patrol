from typing import Annotated

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.main import get_session
from src.services.event_producer import EventProducer

AsyncDbSessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_event_producer(session: AsyncDbSessionDep) -> EventProducer:
    return EventProducer(session, source="API")


EventProducerDep = Annotated[EventProducer, Depends(get_event_producer)]
