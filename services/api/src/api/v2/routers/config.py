# Included in main.py under /api/v2. The stream is specified by the
# positioning-interface contract.
from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter(tags=["config"])


class AtRiskThreshold(BaseModel):
    at_risk_threshold_secs: int


@router.get("/config/at-risk-threshold")
async def stream(request: Request) -> AtRiskThreshold:
    return AtRiskThreshold(at_risk_threshold_secs=600)
