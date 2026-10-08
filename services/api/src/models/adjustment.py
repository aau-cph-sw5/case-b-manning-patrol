from sqlmodel import SQLModel, Field
from enum import StrEnum
from datetime import datetime
from uuid import UUID

class EventType(StrEnum):
    CONNECT_EVENT = "connection"
    DISCONNECT_EVENT = "disconnection"
    START_EVENT = "start"
    STOP_EVENT = "stop"
    ADJUSTMENT_EVENT = "adjustment"

class Adjustment(SQLModel, table=True):
    adjustment_id: UUID = Field(primary_key=True)
    actor: str
    reason: str
    author: str
    server_timestamp: datetime
    corrected_fact_type: EventType
    corrected_beacon_id: str
    corrected_occurred_at: datetime