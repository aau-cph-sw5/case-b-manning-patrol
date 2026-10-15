from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.main import get_session
from src.models.event import EventType
from src.services.producer import MainProducer

router = APIRouter(tags=["positioning-ingestion"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


class ConnectionEvent(BaseModel):
    android_id: str
    beacon_id: str
    timestamp: datetime


class PatrolSessionEvent(BaseModel):
    android_id: str
    timestamp: datetime


# TODO: Connection needs to return Area
@router.post("/connection/connect", status_code=status.HTTP_201_CREATED)
async def connection_event(connection_event: ConnectionEvent, session: SessionDep):
    event_model = await MainProducer.append_event(
        session=session,
        event_type=EventType.CONNECT_EVENT,
        actor=connection_event.android_id,
        beacon=connection_event.beacon_id,
        device_timestamp=connection_event.timestamp,
        source="API",
    )
    return event_model


@router.post("/connection/disconnect", status_code=status.HTTP_201_CREATED)
async def disconnection_event(connection_event: ConnectionEvent, session: SessionDep):
    event_model = await MainProducer.append_event(
        session=session,
        event_type=EventType.DISCONNECT_EVENT,
        actor=connection_event.android_id,
        beacon=connection_event.beacon_id,
        device_timestamp=connection_event.timestamp,
        source="API",
    )
    return event_model


@router.post("/patrol-session/start", status_code=status.HTTP_201_CREATED)
async def patrol_session_start_event(
    patrol_session_event: PatrolSessionEvent, session: SessionDep
):
    event_model = await MainProducer.append_event(
        session=session,
        event_type=EventType.START_EVENT,
        actor=patrol_session_event.android_id,
        device_timestamp=patrol_session_event.timestamp,
        source="API",
    )
    return event_model


@router.post("/patrol-session/stop", status_code=status.HTTP_201_CREATED)
async def patrol_session_stop_event(
    patrol_session_event: PatrolSessionEvent, session: SessionDep
):
    event_model = await MainProducer.append_event(
        session=session,
        event_type=EventType.STOP_EVENT,
        actor=patrol_session_event.android_id,
        device_timestamp=patrol_session_event.timestamp,
        source="API",
    )
    await MainProducer.close_open_connections(
        session=session,
        actor=patrol_session_event.android_id,
        device_timestamp=patrol_session_event.timestamp,
        source="API",
    )
    return event_model
