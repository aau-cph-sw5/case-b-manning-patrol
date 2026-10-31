from uuid import UUID

from sqlmodel import Field, SQLModel


class Train(SQLModel, table=True):
    id: UUID = Field(primary_key=True)
    slug: str
    beacon_id: UUID = Field(unique=True)
