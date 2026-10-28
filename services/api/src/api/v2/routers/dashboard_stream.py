from collections.abc import AsyncIterable
from datetime import UTC, datetime

from fastapi import APIRouter, Request
from fastapi.sse import EventSourceResponse, ServerSentEvent

from src.models.coverage import StationCoverageReport
from src.services.coverage.coverage_updater import CoverageUpdater
from src.services.coverage.dashboard_presenter import DashboardPresenter
from src.services.coverage.sse_broadcaster import SseCoverageBroadcaster

router = APIRouter(tags=["positioning-interface"])


# Included in main.py under /api/v2. The stream is specified by the
# positioning-interface contract.
@router.get("/dashboard/stream", response_class=EventSourceResponse)
async def stream(request: Request) -> AsyncIterable[ServerSentEvent]:
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
    dashboard = presenter.present(reports, sent_at=datetime.now(UTC))
    return ServerSentEvent(data=dashboard, event="dashboard")
