"""Endpoints for the at-risk threshold setting.

Mounted under /api/v2 in main.py. The endpoints are specified by the
positioning-interface contract.
"""

from typing import Annotated

from fastapi import APIRouter, Depends

from src.api.v2.config_schemas.at_risk_treshold import AtRiskThreshold
from src.api.v2.dependencies import AsyncDbSessionDep, ConfigServiceDep
from src.authorization.dependencies import require_permission
from src.security.current_user import User

router = APIRouter(tags=["config"])


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
    threshold: AtRiskThreshold,
    service: ConfigServiceDep,
) -> AtRiskThreshold:
    """Change the at-risk threshold. It must be at least 1 minute."""
    minutes = await service.set_at_risk_threshold_minutes(
        threshold.at_risk_threshold_minutes
    )
    return AtRiskThreshold(at_risk_threshold_minutes=minutes)
