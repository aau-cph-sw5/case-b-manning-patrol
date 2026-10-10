from sqlmodel import JSON, Column, Field, SQLModel


class Line(SQLModel, table=True):
    id: str | None = Field(default=None, primary_key=True)
    name: str
