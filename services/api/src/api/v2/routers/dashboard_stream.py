"""Server-sent events stream of station coverage and the at-risk threshold."""

import asyncio
from collections.abc import AsyncIterable
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.sse import EventSourceResponse, ServerSentEvent

from src.api.v2.schemas.config import AtRiskThreshold
from src.authorization.dependencies import require_permission
from src.domain.coverage import StationCoverageReport
from src.security.current_user import User
from src.services.config.at_risk_threshold_broadcaster import AtRiskThresholdBroadcaster
from src.services.station_coverage.coverage_updater import CoverageUpdater
from src.services.station_coverage.dashboard_presenter import DashboardPresenter
from src.services.station_coverage.sse_broadcaster import SseCoverageBroadcaster

router = APIRouter(tags=["positioning-interface"])


@router.get("/dashboard/stream", response_class=EventSourceResponse)
async def stream(
    request: Request,
    user: Annotated[User, Depends(require_permission("station_manning_coverage_view"))],
) -> AsyncIterable[ServerSentEvent]:
    """Stream the dashboard as `dashboard` events and the threshold as
    `at-risk-threshold` events.

    The latest known coverage and the current at-risk threshold are sent as
    soon as the client connects. After that a `dashboard` event is sent every
    time coverage is recalculated: after each ingested event and every 5
    seconds on the clock ticks. An `at-risk-threshold` event is sent every
    time the threshold is changed through POST /api/v2/config/at-risk-threshold,
    so clients can re-colour their areas under the new threshold. Trains are
    served on their own stream, `/trains/stream`.
    """
    broadcaster: SseCoverageBroadcaster = request.app.state.sse_broadcaster
    threshold_broadcaster: AtRiskThresholdBroadcaster = (
        request.app.state.at_risk_threshold_broadcaster
    )
    updater: CoverageUpdater = request.app.state.coverage_updater
    presenter: DashboardPresenter = request.app.state.dashboard_presenter
    coverage_queue = broadcaster.subscribe()
    threshold_queue = threshold_broadcaster.subscribe()
    try:
        yield _dashboard_event(presenter, updater.snapshot())
        yield _threshold_event(threshold_broadcaster.current())
        while True:
            ready = await _wait_for_refresh(coverage_queue, threshold_queue)
            if coverage_queue in ready:
                yield _dashboard_event(presenter, updater.snapshot())
            if threshold_queue in ready:
                yield _threshold_event(threshold_broadcaster.current())
    finally:
        broadcaster.unsubscribe(coverage_queue)
        threshold_broadcaster.unsubscribe(threshold_queue)


async def _wait_for_refresh(*queues: asyncio.Queue) -> set[asyncio.Queue]:
    """Block until any queue has an item and return every queue that has one.

    Each queue is drained, so a burst of updates coalesces into one event per
    queue per loop iteration.
    """
    tasks = {asyncio.create_task(queue.get()): queue for queue in queues}
    try:
        done, _pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    finally:
        for task in tasks:
            task.cancel()
    ready = {tasks[task] for task in done}
    for queue in queues:
        while not queue.empty():
            queue.get_nowait()
            ready.add(queue)
    return ready


def _dashboard_event(
    presenter: DashboardPresenter,
    station_reports: list[StationCoverageReport],
) -> ServerSentEvent:
    dashboard = presenter.to_dashboard(station_reports, sent_at=datetime.now(UTC))
    return ServerSentEvent(data=dashboard, event="dashboard")


def _threshold_event(minutes: int) -> ServerSentEvent:
    threshold = AtRiskThreshold(at_risk_threshold_minutes=minutes)
    return ServerSentEvent(data=threshold, event="at-risk-threshold")
