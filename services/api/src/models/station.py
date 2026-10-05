from sqlmodel import Field, Relationship, SQLModel

from .patrol_area import PatrolArea


class Station(SQLModel, table=True):
    id: str | None = Field(default=None, primary_key=True, required=True)
    name: str
    line_ids: list[str]
