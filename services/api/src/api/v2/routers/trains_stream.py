"""Server-sent events stream of train manning."""

import asyncio
from collections.abc import AsyncIterable
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.sse import EventSourceResponse, ServerSentEvent

from src.authorization.dependencies import require_permission
from src.domain.train_manning import TrainManningReport
from src.security.current_user import User
from src.services.train_manning.train_manning_publisher import (
    SseTrainManningBroadcaster,
)
from src.services.train_manning.train_manning_updater import TrainManningUpdater
from src.services.train_manning.trains_update_presenter import TrainsUpdatePresenter

router = APIRouter(tags=["positioning-interface"])


@router.get("/trains/stream", response_class=EventSourceResponse)
async def stream(
    request: Request,
    user: Annotated[User, Depends(require_permission("train_manning_coverage_view"))],
) -> AsyncIterable[ServerSentEvent]:
    """Stream train manning as server-sent `trains` events.

    The latest known train manning is sent as soon as the client connects.
    After that a new event is sent every time manning is recalculated: after
    each ingested event and every 5 seconds on the clock ticks.
    """
    broadcaster: SseTrainManningBroadcaster = (
        request.app.state.train_manning_broadcaster
    )
    updater: TrainManningUpdater = request.app.state.train_manning_updater
    presenter: TrainsUpdatePresenter = request.app.state.trains_update_presenter
    queue = broadcaster.subscribe()
    stream = SSETrainStream(broadcaster, presenter, updater, queue)
    async for event in stream.run_stream():
        yield event


class SSETrainStream:
    def __init__(
        self,
        broadcaster: SseTrainManningBroadcaster,
        presenter: TrainsUpdatePresenter,
        updater: TrainManningUpdater,
        queue: asyncio.Queue,
    ):
        self.broadcaster = broadcaster
        self.presenter = presenter
        self.updater = updater
        self.queue = queue

    async def run_stream(self) -> AsyncIterable[ServerSentEvent]:
        try:
            yield self._trains_event(self.presenter, self.updater.snapshot())
            while True:
                await self._wait_for_refresh()
                yield self._trains_event(self.presenter, self.updater.snapshot())
        finally:
            self.broadcaster.unsubscribe(self.queue)

    async def _wait_for_refresh(self) -> None:
        task = asyncio.create_task(self.queue.get())
        try:
            await task
        finally:
            task.cancel()
        while not self.queue.empty():
            await self.queue.get_nowait()

    def _trains_event(
        self,
        presenter: TrainsUpdatePresenter,
        train_reports: list[TrainManningReport],
    ) -> ServerSentEvent:
        trains_update = presenter.to_trains_update(
            train_reports, sent_at=datetime.now(UTC)
        )
        return ServerSentEvent(data=trains_update, event="trains")
