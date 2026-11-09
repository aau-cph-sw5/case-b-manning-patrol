from sqlmodel import Field, SQLModel


class Station(SQLModel, table=True):
    id: str | None = Field(default=None, primary_key=True)
    name: str
