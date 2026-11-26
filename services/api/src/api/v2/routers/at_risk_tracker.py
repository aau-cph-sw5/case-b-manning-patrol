"""At-risk coverage endpoints per shift.

Mounted in main.py under /api/v2; the at-risk-count endpoint is specified by
the positioning-interface contract.
"""

from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel

from src.api.v2.dependencies import AsyncDbSessionDep
from src.authorization.dependencies import require_permission
from src.db.repository.at_risk_log import at_risk_onsets, count_episodes
from src.db.repository.overdue_log import overdue_onsets
from src.security.current_user import User
from src.services.shared.shift_schedule import ShiftSchedule

router = APIRouter(tags=["at-risk"])

ShiftStartQuery = Annotated[
    datetime | None,
    Query(description="ISO 8601 with offset. Defaults to the latest shift."),
]

BUCKET_HOURS = 1


class AtRiskCount(BaseModel):
    """At-risk episodes counted for one shift."""

    shift_start: datetime
    episodes: int


class DurationBucket(BaseModel):
    """Episode counts for the hour of the shift the episodes began in."""

    label: str
    overdue_count: int
    at_risk_count: int


class CoverageSummary(BaseModel):
    """Histogram of when overdue and at-risk episodes began during one shift."""

    shift_start: datetime
    buckets: list[DurationBucket]


@router.get("/coverage/at-risk-count")
async def get_at_risk_count(
    request: Request,
    session: AsyncDbSessionDep,
    user: Annotated[User, Depends(require_permission("at_risk_count_view"))],
    shift_start: ShiftStartQuery = None,
) -> AtRiskCount:
    """Count at-risk episodes for the latest shift, or the given shift start."""
    schedule: ShiftSchedule = request.app.state.shift_schedule
    resolved = shift_start or schedule.latest_shift(datetime.now(UTC)).start
    episodes = await count_episodes(session, resolved)
    return AtRiskCount(shift_start=resolved, episodes=episodes)


def _bucket_label(hours: int) -> str:
    """Return the ``H:00-H:59`` label of the bucket starting at ``hours``."""
    return f"{hours}:00-{hours}:59"


def _bucket_durations(durations: list[timedelta]) -> dict[int, int]:
    """Return how many durations fall in each one-hour bucket."""
    counts: dict[int, int] = {}
    for duration in durations:
        hours = int(duration.total_seconds() // 3600)
        counts[hours] = counts.get(hours, 0) + 1
    return counts


@router.get("/coverage/summary")
async def get_coverage_summary(
    request: Request,
    session: AsyncDbSessionDep,
    user: Annotated[User, Depends(require_permission("coverage_summary_view"))],
    shift_start: ShiftStartQuery = None,
) -> CoverageSummary:
    """Summarize when overdue and at-risk episodes began during one shift.

    Defaults to the latest shift. Each bucket holds the episodes that began
    in that whole hour of the shift; buckets run from zero to the latest
    onset and are zero-filled in between. Overdue episodes count at their
    ``overdue_at``, at-risk episodes at their ``at_risk_at``.
    """
    schedule: ShiftSchedule = request.app.state.shift_schedule
    now = datetime.now(UTC)
    if shift_start is None:
        shift = schedule.latest_shift(now)
    else:
        day = shift_start.astimezone(schedule.timezone).date()
        shift = schedule.shift_on(day)
        if shift.start > shift_start:
            shift = schedule.shift_on(day - timedelta(days=1))
    overdue_counts = _bucket_durations(
        await overdue_onsets(session, shift.start, shift.end)
    )
    at_risk_counts = _bucket_durations(await at_risk_onsets(session, shift.start))
    last_bucket = max([*overdue_counts, *at_risk_counts, -1])
    buckets = [
        DurationBucket(
            label=_bucket_label(hours),
            overdue_count=overdue_counts.get(hours, 0),
            at_risk_count=at_risk_counts.get(hours, 0),
        )
        for hours in range(last_bucket + 1)
    ]
    return CoverageSummary(shift_start=shift.start, buckets=buckets)
