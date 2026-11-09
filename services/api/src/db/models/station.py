"""Database table for stations."""

from sqlmodel import Field, SQLModel


class Station(SQLModel, table=True):
    """A metro station."""

    id: str | None = Field(default=None, primary_key=True)
    name: str
