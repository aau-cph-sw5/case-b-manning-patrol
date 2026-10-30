"""Database table for metro lines."""

from sqlmodel import Field, SQLModel


class Line(SQLModel, table=True):
    """A metro line."""

    id: str | None = Field(default=None, primary_key=True)
    name: str
