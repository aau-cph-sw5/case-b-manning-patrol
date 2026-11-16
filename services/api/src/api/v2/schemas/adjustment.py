"""Request and response bodies for the adjustment endpoint."""

from uuid import UUID

from pydantic import AwareDatetime, BaseModel
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models.adjustment import Adjustment, AdjustmentBase
from src.db.models.adjustment_author import AdjustmentAuthor
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
    """A stored correction as returned by the API.

    `android_id`, `reason` and `author` come from the adjustment's author row
    and are None once it has been anonymised.
    """

    adjustment_id: UUID
    android_id: UUID | None
    reason: str | None
    author: str | None
    corrected_fact: CorrectedFact

    @classmethod
    async def from_adjustment(
        cls, adjustment: Adjustment, session: AsyncSession
    ) -> "AdjustmentEventStored":
        """Build the API response from an adjustment table row."""
        author_result = await session.exec(
            select(AdjustmentAuthor).where(
                AdjustmentAuthor.adjustment_id == adjustment.adjustment_id
            )
        )
        author_info = author_result.first()

        return cls(
            adjustment_id=adjustment.adjustment_id,
            target_event_id=adjustment.target_event_id,
            android_id=author_info.android_id if author_info else None,
            reason=author_info.reason if author_info else None,
            author=author_info.author if author_info else None,
            server_timestamp=adjustment.server_timestamp,
            source=adjustment.source,
            corrected_fact=CorrectedFact(
                fact_type=adjustment.corrected_fact_type,
                beacon_id=adjustment.corrected_beacon_id,
                occurred_at=adjustment.corrected_occured_at,
            ),
        )
