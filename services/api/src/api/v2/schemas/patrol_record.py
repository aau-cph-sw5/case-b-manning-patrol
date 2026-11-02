"""Response bodies for the patrol record endpoint."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel


class Status(Enum):
    """Whether a record is still open or has been closed by a disconnect."""

    OPEN = "open"
    CLOSED = "closed"


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

    `ended_at` is None while the record is open, and `duration_secs` is measured
    up to the time the response was built.
    """

    android_id: UUID
    beacon_id: UUID
    started_at: datetime
    ended_at: datetime | None
    duration_secs: int
    min_patrol_duration_secs: int
    patrolled: bool
    status: Status
    area: RecordArea


class RecordList(BaseModel):
    """A steward's records for the current shift and the time they were built."""

    records: list[Record]
    time: datetime
