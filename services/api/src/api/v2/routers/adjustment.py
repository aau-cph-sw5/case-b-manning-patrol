from fastapi import APIRouter, Request, status

from src.api.v2.dependencies import EventProducerDep
from src.api.v2.schemas.adjustment import AdjustmentEventCreate, AdjustmentEventStored
from src.services.train_manning.train_manning_updater import TrainManningUpdater

router = APIRouter(tags=["adjustment"])


@router.post("/adjustment", status_code=status.HTTP_201_CREATED)
async def adjustment_event(
    adjustment_event: AdjustmentEventCreate,
    producer: EventProducerDep,
    request: Request,
) -> AdjustmentEventStored:
    adjustment = await producer.append_adjustment(
        android_id=adjustment_event.android_id,
        corrected_fact=adjustment_event.corrected_fact,
        reason=adjustment_event.reason,
        author=adjustment_event.author,
        target_event_id=adjustment_event.target_event_id,
    )
    train_manning_updater: TrainManningUpdater = request.app.state.train_manning_updater
    await train_manning_updater.refresh()
    return adjustment
