"""Endpoints for the at-risk threshold setting.

Mounted under /api/v2 in main.py. The endpoints are specified by the
positioning-interface contract.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.api.v2.dependencies import AsyncDbSessionDep
from src.db.repository.config import (
    get_or_create_config,
    set_at_risk_threshold_minutes,
)

router = APIRouter(tags=["config"])


class AtRiskThreshold(BaseModel):
    """Minutes left before an area is overdue at which it counts as at risk."""

    at_risk_threshold_minutes: int = Field(ge=1)


@router.get("/config/at-risk-threshold")
async def get_at_risk_threshold(session: AsyncDbSessionDep) -> AtRiskThreshold:
    """Return the at-risk threshold, creating the default of 10 minutes if unset."""
    config = await get_or_create_config(session)
    return AtRiskThreshold(at_risk_threshold_minutes=config.at_risk_threshold_minutes)


@router.post("/config/at-risk-threshold")
async def set_at_risk_threshold(
    threshold: AtRiskThreshold, session: AsyncDbSessionDep
) -> AtRiskThreshold:
    """Change the at-risk threshold. It must be at least 1 minute."""
    config = await set_at_risk_threshold_minutes(
        session, minutes=threshold.at_risk_threshold_minutes
    )
    return AtRiskThreshold(at_risk_threshold_minutes=config.at_risk_threshold_minutes)
