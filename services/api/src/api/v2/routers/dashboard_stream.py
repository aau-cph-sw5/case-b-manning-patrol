import asyncio
from collections.abc import AsyncIterable
from datetime import UTC, datetime

from fastapi import APIRouter, Request
from fastapi.sse import EventSourceResponse, ServerSentEvent

from src.domain.coverage import StationCoverageReport
from src.domain.train_manning import TrainManningReport
from src.services.station_coverage.coverage_updater import CoverageUpdater
from src.services.station_coverage.dashboard_presenter import DashboardPresenter
from src.services.station_coverage.sse_broadcaster import SseCoverageBroadcaster
from src.services.train_manning.train_manning_publisher import (
    SseTrainManningBroadcaster,
)
from src.services.train_manning.train_manning_updater import TrainManningUpdater

router = APIRouter(tags=["positioning-interface"])


@router.get("/dashboard/stream", response_class=EventSourceResponse)
async def stream(request: Request) -> AsyncIterable[ServerSentEvent]:
    coverage_broadcaster: SseCoverageBroadcaster = request.app.state.sse_broadcaster
    train_broadcaster: SseTrainManningBroadcaster = (
        request.app.state.train_manning_broadcaster
    )
    coverage_updater: CoverageUpdater = request.app.state.coverage_updater
    train_updater: TrainManningUpdater = request.app.state.train_manning_updater
    presenter: DashboardPresenter = request.app.state.dashboard_presenter
    coverage_queue = coverage_broadcaster.subscribe()
    train_queue = train_broadcaster.subscribe()
    try:
        yield _dashboard_event(
            presenter, coverage_updater.snapshot(), train_updater.snapshot()
        )
        while True:
            await _wait_for_any_refresh(coverage_queue, train_queue)
            yield _dashboard_event(
                presenter, coverage_updater.snapshot(), train_updater.snapshot()
            )
    finally:
        coverage_broadcaster.unsubscribe(coverage_queue)
        train_broadcaster.unsubscribe(train_queue)


async def _wait_for_any_refresh(*queues: asyncio.Queue) -> None:
    tasks = [asyncio.create_task(queue.get()) for queue in queues]
    try:
        await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    finally:
        for task in tasks:
            task.cancel()
    for queue in queues:
        while not queue.empty():
            queue.get_nowait()


def _dashboard_event(
    presenter: DashboardPresenter,
    station_reports: list[StationCoverageReport],
    train_reports: list[TrainManningReport],
) -> ServerSentEvent:
    dashboard = presenter.to_dashboard(
        station_reports, train_reports, sent_at=datetime.now(UTC)
    )
    return ServerSentEvent(data=dashboard, event="dashboard")
