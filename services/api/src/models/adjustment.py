from datetime import datetime
from uuid import UUID

from sqlmodel import Field, SQLModel

from src.models.event import EventType


class Adjustment(SQLModel, table=True):
    adjustment_id: UUID = Field(primary_key=True)
    target_event_id: UUID | None = Field(default=None)
    actor: str
    reason: str
    author: str
    server_timestamp: datetime
    corrected_fact_type: EventType
    corrected_beacon_id: str | None
    corrected_occurred_at: datetime
