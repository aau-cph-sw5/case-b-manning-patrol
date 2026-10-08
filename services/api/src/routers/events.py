from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, status
from pydantic import BaseModel

from src.models.event import EventType
from src.services.producer import CorrectedFact, MainProducer

router = APIRouter(tags=["events handler"])
API_VERSION = "v2"
API_PREFIX = f"/api/{API_VERSION}"


class ConnectionEvent(BaseModel):
    android_id: str
    beacon_id: str
    timestamp: datetime


class ShiftEvent(BaseModel):
    android_id: str
    timestamp: datetime


class AdjustmentEvent(BaseModel):
    android_id: str
    corrected_fact: CorrectedFact
    reason: str
    author: str
    target_event_id: UUID | None = None


# TODO: Connection needs to return Area
@router.post(f"{API_PREFIX}/connection/connect", status_code=status.HTTP_201_CREATED)
async def connection_event(connection_event: ConnectionEvent):
    event_model = await MainProducer.append_event(
        event_type=EventType.CONNECT_EVENT,
        actor=connection_event.android_id,
        beacon=connection_event.beacon_id,
        device_timestamp=connection_event.timestamp,
    )
    return event_model


@router.post(f"{API_PREFIX}/connection/disconnect", status_code=status.HTTP_201_CREATED)
async def disconnection_event(connection_event: ConnectionEvent):
    event_model = await MainProducer.append_event(
        event_type=EventType.DISCONNECT_EVENT,
        actor=connection_event.android_id,
        beacon=connection_event.beacon_id,
        device_timestamp=connection_event.timestamp,
    )
    return event_model


@router.post(f"{API_PREFIX}/patrol_session/start", status_code=status.HTTP_201_CREATED)
async def shift_start_event(shift_event: ShiftEvent):
    event_model = await MainProducer.append_event(
        event_type=EventType.START_EVENT,
        actor=shift_event.android_id,
        device_timestamp=shift_event.timestamp,
    )
    return event_model


@router.post(f"{API_PREFIX}/patrol_session/stop", status_code=status.HTTP_201_CREATED)
async def shift_stop_event(shift_event: ShiftEvent):
    event_model = await MainProducer.append_event(
        event_type=EventType.STOP_EVENT,
        actor=shift_event.android_id,
        device_timestamp=shift_event.timestamp,
    )
    return event_model


@router.post(f"{API_PREFIX}/adjustment", status_code=status.HTTP_201_CREATED)
async def adjustment_event(adjustment_event: AdjustmentEvent):
    adjustment_model = await MainProducer.append_adjustment(
        actor=adjustment_event.android_id,
        corrected_fact=adjustment_event.corrected_fact,
        reason=adjustment_event.reason,
        author=adjustment_event.author,
        target_event_id=adjustment_event.target_event_id,
    )
    return adjustment_model
