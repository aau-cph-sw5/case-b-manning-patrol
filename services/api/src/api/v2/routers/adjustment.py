from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.main import get_session
from src.models.event import AdjustmentModel, CorrectedFact
from src.services.producer import MainProducer

router = APIRouter(tags=["adjustment"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


class AdjustmentEvent(BaseModel):
    android_id: UUID
    corrected_fact: CorrectedFact
    reason: str
    author: str
    target_event_id: UUID | None = None


@router.post("/adjustment", status_code=status.HTTP_201_CREATED)
async def adjustment_event(
    adjustment_event: AdjustmentEvent,
    session: SessionDep) -> AdjustmentModel:
    adjustment_model = await MainProducer.append_adjustment(
        session=session,
        android_id=adjustment_event.android_id,
        corrected_fact=adjustment_event.corrected_fact,
        reason=adjustment_event.reason,
        author=adjustment_event.author,
        target_event_id=adjustment_event.target_event_id,
        source="API",
    )

    return adjustment_model
