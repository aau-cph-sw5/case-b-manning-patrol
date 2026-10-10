from sqlmodel import JSON, Column, Field, SQLModel


class StationLine(SQLModel, table=True):
    station_id: str = Field(foreign_key="station.id", primary_key=True)
    line_id: str = Field(foreign_key="line.id", primary_key=True)
