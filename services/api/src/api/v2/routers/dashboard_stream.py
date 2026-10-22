from collections.abc import AsyncIterable
from datetime import UTC, datetime

from fastapi import APIRouter, Request
from fastapi.sse import EventSourceResponse, ServerSentEvent

from src.models.coverage import StationCoverageReport
from src.services.coverage.coverage_updater import CoverageUpdater
from src.services.coverage.dashboard_presenter import DashboardPresenter
from src.services.coverage.sse_broadcaster import SseBroadcaster

router = APIRouter(tags=["positioning-interface"])


# Included in main.py under /api/v2. The stream is specified by the
# positioning-interface contract.
@router.get("/dashboard/stream", response_class=EventSourceResponse)
async def stream(request: Request) -> AsyncIterable[ServerSentEvent]:
    """Stream the dashboard to one client over SSE.

    1. Subscribe to the broadcaster to get this connection's queue.
    2. Send updater.snapshot() as the first event, holding every station. No
       await between steps 1 and 2, so no update is missed or sent twice.
    3. Wait on the queue and yield one event per refresh, holding only the
       stations that changed.
    4. When the client disconnects, unsubscribe (in a finally block).

    The updater, the broadcaster and the presenter are taken from
    request.app.state.
    """
    broadcaster: SseBroadcaster = request.app.state.sse_broadcaster
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
