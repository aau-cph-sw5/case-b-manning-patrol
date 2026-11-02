"""Request and response bodies for the adjustment endpoint."""

from uuid import UUID

from pydantic import AwareDatetime, BaseModel

from src.db.models.adjustment import Adjustment, AdjustmentBase
from src.domain.event import EventType


class CorrectedFact(BaseModel):
    """What the event should have recorded.

    `beacon_id` is required when `fact_type` is connect or disconnect.
    """

    fact_type: EventType
    beacon_id: UUID | None = None
    occurred_at: AwareDatetime


class AdjustmentEventCreate(BaseModel):
    """A supervisor's correction; `target_event_id` is the event it corrects."""

    android_id: UUID
    corrected_fact: CorrectedFact
    reason: str
    author: str
    target_event_id: UUID | None = None


class AdjustmentEventStored(AdjustmentBase):
    """A stored correction as returned by the API."""

    adjustment_id: UUID
    corrected_fact: CorrectedFact

    @classmethod
    def from_adjustment(cls, adjustment: Adjustment) -> "AdjustmentEventStored":
        """Build the API response from an adjustment table row."""
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
