from datetime import datetime
from uuid import UUID
from sqlmodel import Field, SQLModel

class AdjustmentAuthor(SQLModel, table=True):
    """Separate table to store authors of adjustments to avoid storing PII in adjustments table."""

    adjustment_id: UUID = Field(
        foreign_key="adjustment.adjustment_id",
        primary_key=True
    )
    android_id: UUID | None
    reason: str | None
    author: str | None
    server_timestamp: datetime
    source: str = "api"
    anonymized_at: datetime | None = None