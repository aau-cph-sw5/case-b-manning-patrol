"""Server-sent events stream of station coverage for the dashboard."""

from collections.abc import AsyncIterable
from datetime import UTC, datetime

from fastapi import APIRouter, Request
from fastapi.sse import EventSourceResponse, ServerSentEvent

from src.domain.coverage import StationCoverageReport
from src.services.station_coverage.coverage_updater import CoverageUpdater
from src.services.station_coverage.dashboard_presenter import DashboardPresenter
from src.services.station_coverage.sse_broadcaster import SseCoverageBroadcaster

router = APIRouter(tags=["positioning-interface"])


@router.get("/dashboard/stream", response_class=EventSourceResponse)
async def stream(request: Request) -> AsyncIterable[ServerSentEvent]:
    """Stream the dashboard as server-sent `dashboard` events.

    The latest known coverage is sent as soon as the client connects. After
    that a new event is sent every time coverage is recalculated: after each
    ingested event and every 5 seconds on the clock tick.
    """
    broadcaster: SseCoverageBroadcaster = request.app.state.sse_broadcaster
    updater: CoverageUpdater = request.app.state.coverage_updater
    presenter: DashboardPresenter = request.app.state.dashboard_presenter
    queue = broadcaster.subscribe()
    try:
        yield _dashboard_event(presenter, updater.snapshot())
        while True:
            yield _dashboard_event(presenter, await queue.get())
    finally:
        broadcaster.unsubscribe(queue)


def _dashboard_event(
    presenter: DashboardPresenter, reports: list[StationCoverageReport]
) -> ServerSentEvent:
    dashboard = presenter.to_dashboard(reports, sent_at=datetime.now(UTC))
    return ServerSentEvent(data=dashboard, event="dashboard")
