from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlmodel.ext.asyncio.session import AsyncSession

from src.api.v2.schemas.ingestion import PatrolSessionEvent
from src.db.main import get_session
from src.domain.event import EventType
from src.services.event_producer import EventProducer
from src.services.station_coverage.coverage_updater import CoverageUpdater

router = APIRouter(tags=["patrol-session"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post("/patrol-session/start", status_code=status.HTTP_201_CREATED)
async def patrol_session_start_event(
    patrol_session_event: PatrolSessionEvent, session: SessionDep, request: Request
):
    event = await EventProducer.append_event(
        session=session,
        event_type=EventType.START_EVENT,
        android_id=patrol_session_event.android_id,
        device_timestamp=patrol_session_event.timestamp,
        source="API",
    )
    coverage_updater: CoverageUpdater = request.app.state.coverage_updater
    await coverage_updater.refresh()
    return event


@router.post("/patrol-session/stop", status_code=status.HTTP_201_CREATED)
async def patrol_session_stop_event(
    patrol_session_event: PatrolSessionEvent, session: SessionDep, request: Request
):
    event = await EventProducer.append_event(
        session=session,
        event_type=EventType.STOP_EVENT,
        android_id=patrol_session_event.android_id,
        device_timestamp=patrol_session_event.timestamp,
        source="API",
    )
    await EventProducer.close_open_connections(
        session=session,
        android_id=patrol_session_event.android_id,
        device_timestamp=patrol_session_event.timestamp,
        source="API",
    )
    coverage_updater: CoverageUpdater = request.app.state.coverage_updater
    await coverage_updater.refresh()
    return event
