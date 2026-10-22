from datetime import datetime

from sqlmodel import Field, SQLModel


# One row per OverdueDetected or OverdueCleared. Append-only (ADR-0008): rows are
# inserted, never updated or deleted. entry_id is the entry's stable_entry_id, so
# the primary key also stops the same entry from being logged twice.
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
