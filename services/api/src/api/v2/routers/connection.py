from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlmodel.ext.asyncio.session import AsyncSession

from src.api.v2.schemas.ingestion import ConnectionEvent
from src.db.main import get_session
from src.domain.event import EventType
from src.services.event_producer import EventProducer
from src.services.station_coverage.coverage_updater import CoverageUpdater

router = APIRouter(tags=["connection"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post("/connection/connect", status_code=status.HTTP_201_CREATED)
async def connection_event(
    connection_event: ConnectionEvent, session: SessionDep, request: Request
):
    event = await EventProducer.append_event(
        session=session,
        event_type=EventType.CONNECT_EVENT,
        android_id=connection_event.android_id,
        beacon_id=connection_event.beacon_id,
        device_timestamp=connection_event.timestamp,
        source="API",
    )
    coverage_updater: CoverageUpdater = request.app.state.coverage_updater
    await coverage_updater.refresh()
    return event


@router.post("/connection/disconnect", status_code=status.HTTP_201_CREATED)
async def disconnection_event(
    connection_event: ConnectionEvent, session: SessionDep, request: Request
):
    event = await EventProducer.append_event(
        session=session,
        event_type=EventType.DISCONNECT_EVENT,
        android_id=connection_event.android_id,
        beacon_id=connection_event.beacon_id,
        device_timestamp=connection_event.timestamp,
        source="API",
    )
    coverage_updater: CoverageUpdater = request.app.state.coverage_updater
    await coverage_updater.refresh()
    return event
