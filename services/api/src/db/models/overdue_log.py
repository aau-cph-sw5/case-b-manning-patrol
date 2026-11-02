from datetime import datetime

from sqlmodel import Field, SQLModel


class OverdueLogEntry(SQLModel, table=True):
    __tablename__ = "overdue_log"

    entry_id: str = Field(primary_key=True)
    entry_type: str
    station_id: str | None
    area_id: str
    area_kind: str
    overdue_at: datetime
    detected_at: datetime | None
    last_covered_at: datetime | None
    cleared_at: datetime | None
    source: str
