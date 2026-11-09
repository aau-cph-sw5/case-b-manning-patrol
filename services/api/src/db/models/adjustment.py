"""Database table for supervisor adjustments."""

from datetime import datetime
from uuid import UUID

from sqlmodel import Field, SQLModel

from src.domain.event import EventType


class AdjustmentBase(SQLModel):
    """Fields shared by the adjustment table and the API response."""

    target_event_id: UUID | None = None
    android_id: UUID
    reason: str
    author: str
    server_timestamp: datetime
    source: str


class Adjustment(AdjustmentBase, table=True):
    """A stored correction of a steward event; the event itself is not changed."""

    adjustment_id: UUID = Field(primary_key=True)
    corrected_fact_type: EventType
    corrected_beacon_id: UUID | None
    corrected_occured_at: datetime
