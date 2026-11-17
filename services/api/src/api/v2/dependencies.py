"""FastAPI dependencies shared by the v2 routers."""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.main import engine
from src.services.config.config_service import ConfigService
from src.services.event_store.event_producer import EventProducer


async def get_async_db_session() -> AsyncGenerator[AsyncSession]:
    """Yield a database session that lives for one request.

    Objects stay readable after commit so routes can return them.
    """
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


AsyncDbSessionDep = Annotated[AsyncSession, Depends(get_async_db_session)]


def get_event_producer(session: AsyncDbSessionDep) -> EventProducer:
    """Return an event producer that tags new rows with source "API"."""
    return EventProducer(session, source="API")


EventProducerDep = Annotated[EventProducer, Depends(get_event_producer)]


def get_config_service(session: AsyncDbSessionDep) -> ConfigService:
    """Return the config service bound to the request's database session."""
    return ConfigService(session)


ConfigServiceDep = Annotated[ConfigService, Depends(get_config_service)]
