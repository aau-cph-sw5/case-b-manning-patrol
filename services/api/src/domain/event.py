from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class EventType(StrEnum):
    CONNECT_EVENT = "connect"
    DISCONNECT_EVENT = "disconnect"
    START_EVENT = "shift_start"
    STOP_EVENT = "shift_stop"


@dataclass(frozen=True)
class EventRecord:
    """A steward event as used by the coverage calculation.

    ``device_timestamp`` is when the phone saw the event and is the time
    coverage is based on; ``server_timestamp`` is when the backend received
    it. ``beacon_id`` is normally None for START and STOP events.
    """

    event_id: UUID
    event_type: EventType
    android_id: UUID
    beacon_id: UUID | None
    device_timestamp: datetime
    server_timestamp: datetime
