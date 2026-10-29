from datetime import datetime
from uuid import UUID

from sqlmodel import Field, SQLModel

from src.domain.event import EventType


class Event(SQLModel, table=True):
    event_id: UUID = Field(primary_key=True)
    event_type: EventType
    android_id: UUID
    beacon_id: UUID | None
    device_timestamp: datetime
    server_timestamp: datetime
    source: str
