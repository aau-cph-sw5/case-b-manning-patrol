from uuid import UUID

from sqlmodel import Field, SQLModel

from src.db.models.line import Line


class Train(SQLModel, table=True):
    train_id: str | None = Field(default=None, foreign_key="station.id")
    beacon_id: UUID | None = Field(default=None, primary_key=True)
    lines: list[Line]