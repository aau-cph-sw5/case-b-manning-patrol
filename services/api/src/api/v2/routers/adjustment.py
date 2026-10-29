from fastapi import APIRouter, status

from src.api.v2.dependencies import EventProducerDep
from src.api.v2.schemas.adjustment import AdjustmentEventCreate, AdjustmentEventStored

router = APIRouter(tags=["adjustment"])


@router.post("/adjustment", status_code=status.HTTP_201_CREATED)
async def adjustment_event(
    adjustment_event: AdjustmentEventCreate, producer: EventProducerDep
) -> AdjustmentEventStored:
    adjustment = await producer.append_adjustment(
        android_id=adjustment_event.android_id,
        corrected_fact=adjustment_event.corrected_fact,
        reason=adjustment_event.reason,
        author=adjustment_event.author,
        target_event_id=adjustment_event.target_event_id,
    )

    return adjustment
