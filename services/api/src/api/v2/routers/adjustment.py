"""Endpoint for supervisor corrections to recorded events."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from src.api.v2.dependencies import EventProducerDep
from src.api.v2.schemas.adjustment import AdjustmentEventCreate, AdjustmentEventStored
from src.authorization.dependencies import require_permission
from src.security.current_user import User
from src.services.train_manning.train_manning_updater import TrainManningUpdater

router = APIRouter(tags=["adjustment"])


@router.post("/adjustment", status_code=status.HTTP_201_CREATED)
async def adjustment_event(
    adjustment_event: AdjustmentEventCreate,
    producer: EventProducerDep,
    request: Request,
    user: Annotated[
        User, Depends(require_permission("presence.all.own_lines.current_shift"))
    ],
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
    train_manning_updater: TrainManningUpdater = request.app.state.train_manning_updater
    await train_manning_updater.refresh()
    return adjustment
