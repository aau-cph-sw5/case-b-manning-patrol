from uuid import UUID

from sqlmodel import Field, SQLModel

from src.domain.patrol_area import AreaKind


class PatrolArea(SQLModel, table=True):
    beacon_id: UUID | None = Field(default=None, primary_key=True)
    station_id: str | None = Field(default=None, foreign_key="station.id")
    area_id: str
    area_kind: AreaKind
