from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlmodel import Field, SQLModel


class EventType(StrEnum):
    CONNECT_EVENT = "connect"
    DISCONNECT_EVENT = "disconnect"
    START_EVENT = "shift_start"
    STOP_EVENT = "shift_stop"
    ADJUSTMENT_EVENT = "adjustment"


class Event(SQLModel, table=True):
    event_id: UUID = Field(primary_key=True)
    event_type: EventType
    actor: str
    beacon: str | None
    device_timestamp: datetime
    server_timestamp: datetime
