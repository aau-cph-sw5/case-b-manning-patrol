from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlmodel import Field, SQLModel


class EventType(StrEnum):
    CONNECT_EVENT = "connection"
    DISCONNECT_EVENT = "disconnection"
    START_EVENT = "start"
    STOP_EVENT = "stop"
    ADJUSTMENT_EVENT = "adjustment"


class Event(SQLModel, table=True):
    event_id: UUID = Field(primary_key=True)
    event_type: EventType
    actor: str
    beacon: str | None
    device_timestamp: datetime
    server_timestamp: datetime
