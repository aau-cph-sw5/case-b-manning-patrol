"""Server-sent events stream of instantaneous train manning."""

from collections.abc import AsyncIterable
from datetime import UTC, datetime

from fastapi import APIRouter, Request
from fastapi.sse import EventSourceResponse, ServerSentEvent

from src.domain.train_manning import TrainManningReport
from src.services.station_coverage.dashboard_presenter import DashboardPresenter
from src.services.train_manning.train_manning_publisher import (
    SseTrainManningBroadcaster,
)
from src.services.train_manning.train_manning_updater import TrainManningUpdater

router = APIRouter(tags=["positioning-interface"])


@router.get("/trains/stream", response_class=EventSourceResponse)
async def stream(request: Request) -> AsyncIterable[ServerSentEvent]:
    """Stream train manning as server-sent `trains` events.

    The latest known manning of every train is sent as soon as the client
    connects. After that a new event is sent every time manning is
    recalculated: after each ingested event and every 5 seconds on the
    clock tick.
    """
    broadcaster: SseTrainManningBroadcaster = (
        request.app.state.train_manning_broadcaster
    )
    updater: TrainManningUpdater = request.app.state.train_manning_updater
    presenter: DashboardPresenter = request.app.state.dashboard_presenter
    queue = broadcaster.subscribe()
    try:
        yield _trains_event(presenter, updater.snapshot())
        while True:
            yield _trains_event(presenter, await queue.get())
    finally:
        broadcaster.unsubscribe(queue)


def _trains_event(
    presenter: DashboardPresenter, reports: list[TrainManningReport]
) -> ServerSentEvent:
    update = presenter.to_trains_update(reports, sent_at=datetime.now(UTC))
    return ServerSentEvent(data=update, event="trains")
