"""Request and response bodies for the steward app's event endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import AwareDatetime, BaseModel

from src.db.models.event import Event
from src.domain.event import EventType


class ConnectionEvent(BaseModel):
    """A phone connecting to or leaving a beacon; `timestamp` is device time."""

    android_id: UUID
    beacon_id: UUID
    timestamp: AwareDatetime


class PatrolSessionEvent(BaseModel):
    """A steward starting or ending a patrol; `timestamp` is device time."""

    android_id: UUID
    timestamp: AwareDatetime


class StoredEvent(BaseModel):
    """An appended event as returned to the steward app.

    `android_id` is echoed from the request; the stored row only holds a
    per-shift steward reference. `beacon_id` is None for patrol session
    events.
    """

    event_id: UUID
    event_type: EventType
    android_id: UUID
    beacon_id: UUID | None
    device_timestamp: datetime
    server_timestamp: datetime
    source: str

    @classmethod
    def from_event(cls, event: Event, android_id: UUID) -> "StoredEvent":
        """Build the response for ``event``, sent by device ``android_id``."""
        return cls(
            event_id=event.event_id,
            event_type=event.event_type,
            android_id=android_id,
            beacon_id=event.beacon_id,
            device_timestamp=event.device_timestamp,
            server_timestamp=event.server_timestamp,
            source=event.source,
        )
