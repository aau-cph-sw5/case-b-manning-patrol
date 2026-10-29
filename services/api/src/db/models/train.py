from uuid import UUID

from sqlmodel import Field, SQLModel


class Train(SQLModel, table=True):
    id: str | None = Field(default=None, primary_key=True)
    beacon_id: UUID = Field(unique=True)
