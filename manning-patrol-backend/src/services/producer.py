import uuid
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel


class EventType(StrEnum):
    CONNECT_EVENT = 'connection'
    DISCONNECT_EVENT = 'disconnection'
    START_EVENT = 'start'
    STOP_EVENT = 'stop'
    ADJUSTMENT_EVENT = 'adjustment'

class EventModel(BaseModel):
    event_id: str
    event_type: EventType
    actor: str
    beacon: str | None
    device_timestamp: str
    server_timestamp: str
    #source: api/simulator/import


class MainProducer:
    @staticmethod
    async def appendConncetion(
        event_type: EventType,
        actor: str,
        beacon: str,
        device_timestamp: str,
    ) -> EventModel:
        event_model = EventModel(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            actor=actor,
            beacon=beacon,
            device_timestamp=device_timestamp,
            server_timestamp=_now_utc_iso(),
        )
        await _send_model_tester(event_model)
        return event_model
    
    @staticmethod
    async def appendShift(
            event_type: EventType,
            actor: str,
            device_timestamp: str,
        ) -> EventModel:
            event_model = EventModel(
                event_id=str(uuid.uuid4()),
                event_type=event_type,
                actor=actor,
                beacon=None,
                device_timestamp=device_timestamp,
                server_timestamp=_now_utc_iso(),
            )
            await _send_model_tester(event_model)
            return event_model

async def _send_model_tester(event_model: EventModel) -> EventModel:
    print(event_model)
    return event_model


def _now_utc_iso() -> str:
    return datetime.now(UTC).isoformat()


