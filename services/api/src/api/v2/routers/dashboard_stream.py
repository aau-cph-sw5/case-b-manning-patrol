"""Server-sent events stream of station coverage."""

from collections.abc import AsyncIterable
from contextlib import aclosing
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.sse import EventSourceResponse, ServerSentEvent

from src.authorization.dependencies import require_permission
from src.security.current_user import User
from src.services.station_coverage.coverage_updater import CoverageUpdater
from src.services.station_coverage.dashboard_presenter import DashboardPresenter
from src.services.station_coverage.sse_broadcaster import SseCoverageBroadcaster
from src.services.station_coverage.sse_dashboard_stream import SSEDashboardStream

router = APIRouter(tags=["positioning-interface"])


@router.get("/dashboard/stream", response_class=EventSourceResponse)
async def stream(
    request: Request,
    user: Annotated[User, Depends(require_permission("station_manning_coverage_view"))],
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
    stream = SSEDashboardStream(broadcaster, presenter, updater, queue)
    async with aclosing(stream.run_stream()) as events:
        async for event in events:
            yield event
