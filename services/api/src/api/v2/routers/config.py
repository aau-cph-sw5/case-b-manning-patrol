"""Endpoints for the at-risk threshold setting.

Mounted under /api/v2 in main.py. The endpoints are specified by the
positioning-interface contract.
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from src.api.v2.dependencies import AsyncDbSessionDep, ConfigServiceDep
from src.authorization.dependencies import require_permission
from src.db.repository.config import (
    get_or_create_config,
    set_at_risk_threshold_minutes,
)
from src.security.current_user import User


router = APIRouter(tags=["config"])


class AtRiskThreshold(BaseModel):
    """Minutes left before an area is overdue at which it counts as at risk."""

    at_risk_threshold_minutes: int = Field(ge=1)


@router.get("/config/at-risk-threshold")
async def get_at_risk_threshold(
    service: ConfigServiceDep,
    session: AsyncDbSessionDep,
    user: Annotated[User, Depends(require_permission("at_risk_threshold_view"))],
) -> AtRiskThreshold:
    """Return the at-risk threshold, creating the default of 10 minutes if unset."""
    minutes = await service.get_at_risk_threshold_minutes()
    return AtRiskThreshold(at_risk_threshold_minutes=minutes)


@router.post("/config/at-risk-threshold")
async def set_at_risk_threshold(
    session: AsyncDbSessionDep,
    user: Annotated[User, Depends(require_permission("at_risk_threshold_set"))],
    threshold: AtRiskThreshold, service: ConfigServiceDep
) -> AtRiskThreshold:
    """Change the at-risk threshold. It must be at least 1 minute."""
    minutes = await service.set_at_risk_threshold_minutes(
        threshold.at_risk_threshold_minutes
    )
    return AtRiskThreshold(at_risk_threshold_minutes=minutes)
