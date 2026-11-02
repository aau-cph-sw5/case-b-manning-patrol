"""Database table for the at-risk log."""

from datetime import datetime

from sqlmodel import Field, SQLModel


class AtRiskLogEntry(SQLModel, table=True):
    """A counted at-risk episode in the append-only at-risk log.

    ``entry_id`` is derived from the episode, so the same episode is never
    counted twice, even across restarts.
    """

    __tablename__ = "at_risk_log"

    entry_id: str = Field(primary_key=True)
    station_id: str | None
    area_id: str
    area_kind: str
    at_risk_at: datetime
    overdue_at: datetime
    detected_at: datetime
    shift_start: datetime
    source: str
