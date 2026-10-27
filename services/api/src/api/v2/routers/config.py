# Included in main.py under /api/v2. The endpoints are specified by the
# positioning-interface contract.
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.main import get_session
from src.db.repository.config import (
    get_or_create_config,
    set_at_risk_threshold_minutes,
)

router = APIRouter(tags=["config"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


class AtRiskThreshold(BaseModel):
    at_risk_threshold_minutes: int = Field(ge=1)


@router.get("/config/at-risk-threshold")
async def get_at_risk_threshold(session: SessionDep) -> AtRiskThreshold:
    config = await get_or_create_config(session)
    return AtRiskThreshold(at_risk_threshold_minutes=config.at_risk_threshold_minutes)


@router.post("/config/at-risk-threshold")
async def set_at_risk_threshold(
    threshold: AtRiskThreshold, session: SessionDep
) -> AtRiskThreshold:
    config = await set_at_risk_threshold_minutes(
        session, minutes=threshold.at_risk_threshold_minutes
    )
    return AtRiskThreshold(at_risk_threshold_minutes=config.at_risk_threshold_minutes)
