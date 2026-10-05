from typing import TYPE_CHECKING
from uuid import UUID
from enum import StrEnum

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    # Imported here only for type checking to avoid a circular import:
    # station.py imports PatrolArea from this module.
    from .station import Station


class AreaKind(StrEnum):
    CONCOURSE = "concourse"
    PLATFORM = "platform"


class PatrolArea(SQLModel, table=True):
    beacon_id: UUID | None = Field(default=None, primary_key=True, required=True)
    station_id: str | None = Field(default=None, foreign_key="station.id")
    id: str | None = Field(default=None, required=True)
    area_kind: AreaKind
