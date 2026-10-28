from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import AwareDatetime, BaseModel
from sqlmodel import Field, SQLModel


class EventType(StrEnum):
    CONNECT_EVENT = "connect"
    DISCONNECT_EVENT = "disconnect"
    START_EVENT = "shift_start"
    STOP_EVENT = "shift_stop"
    ADJUSTMENT_EVENT = "adjustment"


class Event(SQLModel, table=True):
    event_id: UUID = Field(primary_key=True)
    event_type: EventType
    android_id: UUID
    beacon_id: UUID | None
    device_timestamp: datetime
    server_timestamp: datetime
    source: str


class CorrectedFact(BaseModel):
    fact_type: EventType
    beacon_id: UUID | None = None
    occurred_at: AwareDatetime


class AdjustmentBase(SQLModel):
    target_event_id: UUID | None = None
    android_id: UUID
    reason: str
    author: str
    server_timestamp: datetime
    source: str


class Adjustment(AdjustmentBase, table=True):
    adjustment_id: UUID = Field(primary_key=True)
    corrected_fact_type: EventType
    corrected_beacon_id: UUID | None
    corrected_occured_at: datetime


class AdjustmentStored(AdjustmentBase):
    """API shape of a stored adjustment, with the corrected fact nested."""

    adjustment_id: UUID
    corrected_fact: CorrectedFact

    @classmethod
    def from_adjustment(cls, adjustment: Adjustment) -> "AdjustmentStored":
        return cls(
            adjustment_id=adjustment.adjustment_id,
            target_event_id=adjustment.target_event_id,
            android_id=adjustment.android_id,
            reason=adjustment.reason,
            author=adjustment.author,
            server_timestamp=adjustment.server_timestamp,
            source=adjustment.source,
            corrected_fact=CorrectedFact(
                fact_type=adjustment.corrected_fact_type,
                beacon_id=adjustment.corrected_beacon_id,
                occurred_at=adjustment.corrected_occured_at,
            ),
        )
