from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class ExpiredTarget(StrEnum):
    """Enum for the target of expired records."""

    STEWARD_SHIFT_IDENTITY = "steward_shift_identity"
    ADJUSTMENT_AUTHOR = "adjustment_author"


class ExpiredRecord(SQLModel, table=True):
    """A record of an expired steward shift or adjustment author."""

    expired_id: UUID = Field(default_factory=uuid4, primary_key=True)
    target: ExpiredTarget
    record_id: UUID
    server_timestamp: datetime
    source: str = "anonymizer"
