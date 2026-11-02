# Included in main.py under /api/v2. Counts at-risk episodes per shift.
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel

from src.api.v2.dependencies import AsyncDbSessionDep
from src.db.repository.at_risk_log import count_episodes
from src.services.station_coverage.shift_schedule import ShiftSchedule

router = APIRouter(tags=["at-risk"])

ShiftStartDep = Annotated[
    datetime | None,
    Query(description="ISO 8601 with offset. Defaults to the latest shift."),
]


class AtRiskCount(BaseModel):
    shift_start: datetime
    episodes: int


@router.get("/coverage/at-risk-count")
async def get_at_risk_count(
    request: Request,
    session: AsyncDbSessionDep,
    shift_start: ShiftStartDep = None,
) -> AtRiskCount:
    """Count at-risk episodes for the latest shift, or the given shift start."""
    schedule: ShiftSchedule = request.app.state.shift_schedule
    resolved = shift_start or schedule.latest_shift(datetime.now(UTC)).start
    episodes = await count_episodes(session, resolved)
    return AtRiskCount(shift_start=resolved, episodes=episodes)
