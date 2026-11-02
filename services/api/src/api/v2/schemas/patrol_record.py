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
    station_id: str
    area_type: AreaType


class Record(BaseModel):
    """One visit by a steward to a patrol area.

    `ended_at` and `duration_secs` are None while the record is open.
    """

    android_id: UUID
    beacon_id: UUID
    started_at: datetime
    ended_at: datetime | None
    duration_secs: int | None
    min_patrol_duration_secs: int
    patrolled: bool
    status: Status
    area: RecordArea


class RecordList(BaseModel):
    """A steward's records for the current shift and the time they were built."""

    records: list[Record]
    time: datetime
