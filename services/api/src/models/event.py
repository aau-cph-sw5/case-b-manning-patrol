from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import AwareDatetime, BaseModel
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
    android_id: UUID
    beacon_id: UUID | None
    device_timestamp: datetime
    server_timestamp: datetime
    source: str


class Adjustment(SQLModel, table=True):
    adjustment_id: UUID = Field(primary_key=True)
    target_event_id: UUID | None = Field(default=None)
    android_id: UUID
    reason: str
    author: str
    server_timestamp: datetime
    corrected_fact_type: EventType
    corrected_beacon_id: UUID | None
    corrected_occured_at: datetime
    source: str


class EventModel(BaseModel):
    event_id: UUID
    event_type: EventType
    android_id: UUID
    beacon_id: UUID | None
    device_timestamp: datetime
    server_timestamp: datetime
    source: str


class CorrectedFact(BaseModel):
    fact_type: EventType
    beacon_id: UUID | None = None
    occurred_at: AwareDatetime


class AdjustmentModel(BaseModel):
    adjustment_id: UUID
    target_event_id: UUID | None = None
    android_id: UUID
    corrected_fact: CorrectedFact
    reason: str
    author: str
    server_timestamp: datetime
    source: str
