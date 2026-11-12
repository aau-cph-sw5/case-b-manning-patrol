"""Server-sent events stream of station coverage."""

import asyncio
from collections.abc import AsyncIterable
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.sse import EventSourceResponse, ServerSentEvent

from src.authorization.dependencies import require_permission
from src.domain.coverage import StationCoverageReport
from src.security.current_user import User
from src.services.station_coverage.coverage_updater import CoverageUpdater
from src.services.station_coverage.dashboard_presenter import DashboardPresenter
from src.services.station_coverage.sse_broadcaster import SseCoverageBroadcaster

router = APIRouter(tags=["positioning-interface"])


@router.get("/dashboard/stream", response_class=EventSourceResponse)
async def stream(
    request: Request,
    user: Annotated[
        User, Depends(require_permission("coverage.all.own_lines.current_shift"))
    ],
) -> AsyncIterable[ServerSentEvent]:
    """Stream the dashboard as server-sent `dashboard` events.

    The latest known coverage is sent as soon as the client connects. After
    that a new event is sent every time coverage is recalculated: after each
    ingested event and every 5 seconds on the clock ticks. Trains are served
    on their own stream, `/trains/stream`.
    """
    broadcaster: SseCoverageBroadcaster = request.app.state.sse_broadcaster
    updater: CoverageUpdater = request.app.state.coverage_updater
    presenter: DashboardPresenter = request.app.state.dashboard_presenter
    queue = broadcaster.subscribe()
    try:
        yield _dashboard_event(presenter, updater.snapshot())
        while True:
            await _wait_for_refresh(queue)
            yield _dashboard_event(presenter, updater.snapshot())
    finally:
        broadcaster.unsubscribe(queue)


async def _wait_for_refresh(queue: asyncio.Queue) -> None:
    task = asyncio.create_task(queue.get())
    try:
        await task
    finally:
        task.cancel()
    while not queue.empty():
        queue.get_nowait()


def _dashboard_event(
    presenter: DashboardPresenter,
    station_reports: list[StationCoverageReport],
) -> ServerSentEvent:
    dashboard = presenter.to_dashboard(station_reports, sent_at=datetime.now(UTC))
    return ServerSentEvent(data=dashboard, event="dashboard")
