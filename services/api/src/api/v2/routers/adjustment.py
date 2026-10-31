"""Endpoint for supervisor corrections to recorded events."""

from fastapi import APIRouter, status

from src.api.v2.dependencies import EventProducerDep
from src.api.v2.schemas.adjustment import AdjustmentEventCreate, AdjustmentEventStored

router = APIRouter(tags=["adjustment"])


@router.post("/adjustment", status_code=status.HTTP_201_CREATED)
async def adjustment_event(
    adjustment_event: AdjustmentEventCreate, producer: EventProducerDep
) -> AdjustmentEventStored:
    """Record a correction to a steward event.

    The original event is not changed; the correction is stored alongside it.
    Returns 400 if a connect or disconnect correction has no `beacon_id`, and
    404 if `target_event_id` is given but no such event exists.
    """
    adjustment = await producer.append_adjustment(
        android_id=adjustment_event.android_id,
        corrected_fact=adjustment_event.corrected_fact,
        reason=adjustment_event.reason,
        author=adjustment_event.author,
        target_event_id=adjustment_event.target_event_id,
    )

    return adjustment
