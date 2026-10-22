from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.main import get_session
from src.models.event import EventType
from src.services.coverage.coverage_updater import CoverageUpdater
from src.services.producer import MainProducer

router = APIRouter(tags=["positioning-ingestion"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


class ConnectionEvent(BaseModel):
    android_id: UUID
    beacon_id: UUID
    timestamp: datetime


class PatrolSessionEvent(BaseModel):
    android_id: UUID
    timestamp: datetime


@router.post("/connection/connect", status_code=status.HTTP_201_CREATED)
async def connection_event(
    connection_event: ConnectionEvent, session: SessionDep, request: Request
):
    event_model = await MainProducer.append_event(
        session=session,
        event_type=EventType.CONNECT_EVENT,
        android_id=connection_event.android_id,
        beacon_id=connection_event.beacon_id,
        device_timestamp=connection_event.timestamp,
        source="API",
    )
    coverage_updater: CoverageUpdater = request.app.state.coverage_updater
    await coverage_updater.refresh()
    return event_model


@router.post("/connection/disconnect", status_code=status.HTTP_201_CREATED)
async def disconnection_event(
    connection_event: ConnectionEvent, session: SessionDep, request: Request
):
    event_model = await MainProducer.append_event(
        session=session,
        event_type=EventType.DISCONNECT_EVENT,
        android_id=connection_event.android_id,
        beacon_id=connection_event.beacon_id,
        device_timestamp=connection_event.timestamp,
        source="API",
    )
    coverage_updater: CoverageUpdater = request.app.state.coverage_updater
    await coverage_updater.refresh()
    return event_model


@router.post("/patrol-session/start", status_code=status.HTTP_201_CREATED)
async def patrol_session_start_event(
    patrol_session_event: PatrolSessionEvent, session: SessionDep, request: Request
):
    event_model = await MainProducer.append_event(
        session=session,
        event_type=EventType.START_EVENT,
        android_id=patrol_session_event.android_id,
        device_timestamp=patrol_session_event.timestamp,
        source="API",
    )
    coverage_updater: CoverageUpdater = request.app.state.coverage_updater
    await coverage_updater.refresh()
    return event_model


@router.post("/patrol-session/stop", status_code=status.HTTP_201_CREATED)
async def patrol_session_stop_event(
    patrol_session_event: PatrolSessionEvent, session: SessionDep, request: Request
):
    event_model = await MainProducer.append_event(
        session=session,
        event_type=EventType.STOP_EVENT,
        android_id=patrol_session_event.android_id,
        device_timestamp=patrol_session_event.timestamp,
        source="API",
    )
    await MainProducer.close_open_connections(
        session=session,
        android_id=patrol_session_event.android_id,
        device_timestamp=patrol_session_event.timestamp,
        source="API",
    )
    coverage_updater: CoverageUpdater = request.app.state.coverage_updater
    await coverage_updater.refresh()
    return event_model
