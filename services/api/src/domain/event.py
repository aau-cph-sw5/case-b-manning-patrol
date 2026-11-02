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
    event_id: UUID
    event_type: EventType
    android_id: UUID
    beacon_id: UUID | None
    device_timestamp: datetime
    server_timestamp: datetime
