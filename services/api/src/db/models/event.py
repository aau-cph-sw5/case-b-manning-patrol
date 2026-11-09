"""Database table for the steward event log."""

from datetime import datetime
from uuid import UUID

from sqlmodel import Field, SQLModel

from src.domain.event import EventType


class Event(SQLModel, table=True):
    """One event from a steward's phone. Rows are only ever inserted.

    ``device_timestamp`` is when the phone saw the event and
    ``server_timestamp`` is when the backend stored it. ``beacon_id`` is
    None for patrol session start and stop events.
    """

    event_id: UUID = Field(primary_key=True)
    event_type: EventType
    android_id: UUID
    beacon_id: UUID | None
    device_timestamp: datetime
    server_timestamp: datetime
    source: str
