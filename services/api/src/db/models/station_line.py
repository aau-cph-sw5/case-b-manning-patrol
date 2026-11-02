"""Database table linking stations to the lines that serve them."""

from sqlmodel import Field, SQLModel


class StationLine(SQLModel, table=True):
    """Records that a line serves a station."""

    station_id: str = Field(foreign_key="station.id", primary_key=True)
    line_id: str = Field(foreign_key="line.id", primary_key=True)
