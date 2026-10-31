import asyncio
from dataclasses import dataclass, field
from typing import Protocol

from src.domain.train_manning import TrainManningReport


class TrainManningPublisher(Protocol):
    def publish(self, reports: list[TrainManningReport]) -> None: ...


@dataclass
class SseTrainManningBroadcaster(TrainManningPublisher):
    _subscribers: set[asyncio.Queue[list[TrainManningReport]]] = field(
        default_factory=set
    )

    def publish(self, reports: list[TrainManningReport]) -> None:
        for queue in self._subscribers:
            queue.put_nowait(reports)

    def subscribe(self) -> asyncio.Queue[list[TrainManningReport]]:
        queue: asyncio.Queue[list[TrainManningReport]] = asyncio.Queue()
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[list[TrainManningReport]]) -> None:
        self._subscribers.discard(queue)
