from enum import StrEnum
from uuid import UUID

from sqlmodel import Field, SQLModel


class AreaKind(StrEnum):
    CONCOURSE = "concourse"
    PLATFORM = "platform"


class PatrolArea(SQLModel, table=True):
    beacon_id: UUID | None = Field(default=None, primary_key=True)
    station_id: str | None = Field(default=None, foreign_key="station.id")
    id: str
    area_kind: AreaKind
