"""Fan out at-risk threshold changes to connected dashboard SSE streams."""

import asyncio


class AtRiskThresholdBroadcaster:
    """Give each dashboard stream its own queue of threshold changes.

    The latest value is kept so a client that connects after a change still
    learns the current threshold from the first event it receives.
    """

    def __init__(self, current_minutes: int) -> None:
        self._current_minutes = current_minutes
        self._subscribers: set[asyncio.Queue[int]] = set()

    def publish(self, minutes: int) -> None:
        """Store ``minutes`` as current and queue it for every subscriber."""
        self._current_minutes = minutes
        for queue in self._subscribers:
            queue.put_nowait(minutes)

    def current(self) -> int:
        """Return the latest published threshold in minutes."""
        return self._current_minutes

    def subscribe(self) -> asyncio.Queue[int]:
        """Register a new client and return the queue it should read from."""
        queue: asyncio.Queue[int] = asyncio.Queue()
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[int]) -> None:
        """Stop sending updates to ``queue``; unknown queues are ignored."""
        self._subscribers.discard(queue)
