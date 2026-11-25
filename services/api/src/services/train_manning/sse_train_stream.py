import asyncio
from collections.abc import AsyncIterable
from datetime import UTC, datetime

from fastapi.sse import ServerSentEvent

from src.domain.train_manning import TrainManningReport
from src.services.train_manning.train_manning_publisher import (
    SseTrainManningBroadcaster,
)
from src.services.train_manning.train_manning_updater import TrainManningUpdater
from src.services.train_manning.trains_update_presenter import TrainsUpdatePresenter


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
            self.queue.get_nowait()

    def _trains_event(
        self,
        presenter: TrainsUpdatePresenter,
        train_reports: list[TrainManningReport],
    ) -> ServerSentEvent:
        trains_update = presenter.to_trains_update(
            train_reports, sent_at=datetime.now(UTC)
        )
        return ServerSentEvent(data=trains_update, event="trains")
