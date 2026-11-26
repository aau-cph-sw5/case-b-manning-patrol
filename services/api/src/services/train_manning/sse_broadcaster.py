"""Fan out train manning reports to connected trains SSE streams."""

import asyncio
from dataclasses import dataclass, field

from src.domain.train_manning import TrainManningReport
from src.services.train_manning.train_manning_publisher import TrainManningPublisher


@dataclass
class SseTrainManningBroadcaster(TrainManningPublisher):
    """Give each server-sent-events client its own queue of train manning updates."""

    _subscribers: set[asyncio.Queue[list[TrainManningReport]]] = field(
        default_factory=set
    )

    def publish(self, reports: list[TrainManningReport]) -> None:
        """Put the reports on every subscriber's queue.

        Queues are unbounded, so a client that stops reading accumulates
        updates until it unsubscribes.
        """
        for queue in self._subscribers:
            queue.put_nowait(reports)

    def subscribe(self) -> asyncio.Queue[list[TrainManningReport]]:
        """Register a new client and return the queue it should read from."""
        queue: asyncio.Queue[list[TrainManningReport]] = asyncio.Queue()
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[list[TrainManningReport]]) -> None:
        """Stop sending updates to ``queue``; unknown queues are ignored."""
        self._subscribers.discard(queue)
