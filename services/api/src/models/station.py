from sqlmodel import JSON, Column, Field, SQLModel


class Station(SQLModel, table=True):
    id: str | None = Field(default=None, primary_key=True)
    name: str
    line_ids: list[str] = Field(sa_column=Column(JSON))
