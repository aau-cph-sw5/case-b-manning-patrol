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
    station_id: str
    area_type: AreaType


class Record(BaseModel):
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
    records: list[Record]
    time: datetime
