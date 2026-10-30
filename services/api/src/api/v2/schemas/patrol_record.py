from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel


class Status(Enum):
    PENDING = "pending"
    REGISTERED = "registered"


class AreaType(Enum):
    PLATFORM = "platform"
    CONCOURCE = "concourse"


class RecordArea(BaseModel):
    area_id: str
    name: str
    line: list[str]
    station_id: str  # Why not just station name??
    area_type: AreaType


class Record(BaseModel):
    android_id: UUID  # Will be given by GET request
    beacon_id: UUID  # Will be fetched from Event tables
    started_at: datetime  # If ConnectionEvent -> derived
    ended_at: datetime | None  # If DisconnectionEvent -> derived
    duration_secs: int | None  # Subtract DisconnetionEvent from ConnectionEvent
    min_patrol_duration_secs: int  # Can only be derived from PatrolArea
    patrolled: bool  # duration_secs >= min_patrol_duration_secs
    status: Status  # Move to frontend perhaps
    area: RecordArea  # Derived from PatrolArea joined Station


class RecordList(BaseModel):
    records: list[Record]
    time: datetime
