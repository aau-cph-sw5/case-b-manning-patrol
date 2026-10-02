from fastapi import APIRouter, status
from pydantic import BaseModel

from src.services.producer import EventType, MainProducer

router = APIRouter(tags=["events handler"])

class ConnectionEvent(BaseModel):
    android_id: str
    beacon_id: str
    timestamp: str

class ShiftEvent(BaseModel):
    android_id: str
    timestamp: str

# TODO: Connection needs to return Area
@router.post("/api/v1/connection/connect", status_code=status.HTTP_201_CREATED)
async def connection_event(connection_event: ConnectionEvent):
    event_model = await MainProducer.appendConncetion(
        event_type=EventType.CONNECT_EVENT,
        actor=connection_event.android_id,
        beacon=connection_event.beacon_id,
        device_timestamp=connection_event.timestamp,
    )
    return event_model

@router.post("/api/v1/connection/disconnect", status_code=status.HTTP_201_CREATED)
async def disconnection_event(connection_event: ConnectionEvent):
    event_model = await MainProducer.appendConncetion(
        event_type=EventType.DISCONNECT_EVENT,
        actor=connection_event.android_id,
        beacon=connection_event.beacon_id,
        device_timestamp=connection_event.timestamp,
    )
    return event_model

@router.post("/api/v1/shift/start", status_code=status.HTTP_201_CREATED)
async def shift_start_event(shift_event: ShiftEvent):
    event_model = await MainProducer.appendShift(
        event_type=EventType.START_EVENT,
        actor=shift_event.android_id,
        device_timestamp=shift_event.timestamp,
    )
    return event_model

@router.post("/api/v1/shift/stop", status_code=status.HTTP_201_CREATED)
async def shift_stop_event(shift_event: ShiftEvent):
    event_model = await MainProducer.appendShift(
        event_type=EventType.STOP_EVENT,
        actor=shift_event.android_id,
        device_timestamp=shift_event.timestamp,
    )
    return event_model
