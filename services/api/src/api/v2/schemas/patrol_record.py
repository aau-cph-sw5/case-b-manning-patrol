"""Response bodies for the patrol record endpoint."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel


class Status(Enum):
    """Whether a record is still open or has been closed by a disconnect."""

    PENDING = "pending"
    REGISTERED = "registered"


class AreaType(Enum):
    """The kind of patrol area a record was made in."""

    PLATFORM = "platform"
    CONCOURSE = "concourse"


class RecordArea(BaseModel):
    """The patrol area a record was made in, named after its station."""

    area_id: str
    name: str
    line: list[str]
    station_id: str  # Why not just station name??
    area_type: AreaType


class Record(BaseModel):
    """One visit by a steward to a patrol area.

    `ended_at` and `duration_secs` are None while the record is pending.
    """

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
    """A steward's records for the current shift and the time they were built."""

    records: list[Record]
    time: datetime
