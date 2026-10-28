from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from src.api.v2.schemas.adjustment import AdjustmentEventCreate, AdjustmentEventStored
from src.db.main import get_session
from src.services.event_producer import EventProducer

router = APIRouter(tags=["adjustment"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post("/adjustment", status_code=status.HTTP_201_CREATED)
async def adjustment_event(
    adjustment_event: AdjustmentEventCreate, session: SessionDep
) -> AdjustmentEventStored:
    adjustment = await EventProducer.append_adjustment(
        session=session,
        android_id=adjustment_event.android_id,
        corrected_fact=adjustment_event.corrected_fact,
        reason=adjustment_event.reason,
        author=adjustment_event.author,
        target_event_id=adjustment_event.target_event_id,
        source="API",
    )

    return adjustment
