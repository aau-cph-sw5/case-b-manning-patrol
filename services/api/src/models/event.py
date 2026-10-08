from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlmodel import Field, SQLModel


class EventType(StrEnum):
    CONNECT_EVENT = "connect"
    DISCONNECT_EVENT = "disconnect"
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


class Adjustment(SQLModel, table=True):
    adjustment_id: UUID = Field(primary_key=True)
    target_event_id: UUID | None = Field(default=None)
    actor: str
    reason: str
    author: str
    server_timestamp: datetime
    corrected_fact_type: EventType
    corrected_beacon_id: str | None
    corrected_occured_at: datetime
