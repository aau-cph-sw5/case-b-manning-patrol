"""Endpoints for the at-risk threshold setting.

Mounted under /api/v2 in main.py. The endpoints are specified by the
positioning-interface contract.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from src.api.v2.dependencies import AsyncDbSessionDep, ConfigServiceDep
from src.api.v2.schemas.config import AtRiskThreshold
from src.authorization.dependencies import require_permission
from src.security.current_user import User
from src.services.config.at_risk_threshold_broadcaster import AtRiskThresholdBroadcaster

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
    request: Request,
    session: AsyncDbSessionDep,
    user: Annotated[User, Depends(require_permission("at_risk_threshold_set"))],
    threshold: AtRiskThreshold,
    service: ConfigServiceDep,
) -> AtRiskThreshold:
    """Change the at-risk threshold. It must be at least 1 minute.

    Every connected dashboard stream is notified with an `at-risk-threshold`
    event, so clients re-colour their areas under the new threshold.
    """
    minutes = await service.set_at_risk_threshold_minutes(
        threshold.at_risk_threshold_minutes
    )
    broadcaster: AtRiskThresholdBroadcaster = (
        request.app.state.at_risk_threshold_broadcaster
    )
    broadcaster.publish(minutes)
    return AtRiskThreshold(at_risk_threshold_minutes=minutes)
