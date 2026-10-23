# Included in main.py under /api/v2. The stream is specified by the
# positioning-interface contract.
from typing import Annotated

from fastapi import APIRouter, Request
from pydantic import BaseModel
from fastapi import APIRouter, Depends, Request, status
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.main import get_session

router = APIRouter(tags=["config"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


class AtRiskThreshold(BaseModel):
    at_risk_threshold_minutes: int


@router.get("/config/at-risk-threshold")
async def at_risk_threshold(request: Request) -> AtRiskThreshold:
    return AtRiskThreshold(at_risk_threshold_minutes=10)


@router.post("/config/at-risk-threshold")
async def at_risk_threshold(
    atRiskThreshHold: AtRiskThreshold, session: SessionDep, request: Request
) -> AtRiskThreshold:
    pass
