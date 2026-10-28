# Included in main.py under /api/v2. The endpoints are specified by the
# positioning-interface contract.
from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.db.main import SessionDep
from src.db.repository.config import (
    get_or_create_config,
    set_at_risk_threshold_minutes,
)

router = APIRouter(tags=["config"])


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
