from sqlmodel import Field, SQLModel


class ExampleItem(SQLModel, table=True):
    """Throwaway table to verify the Postgres setup."""

    id: int | None = Field(default=None, primary_key=True)
    name: str
