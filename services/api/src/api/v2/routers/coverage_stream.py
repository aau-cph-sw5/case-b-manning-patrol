from collections.abc import AsyncIterable

from fastapi import APIRouter, Request
from fastapi.sse import EventSourceResponse, ServerSentEvent

from src.services.coverage.coverage_updater import CoverageUpdater
from src.services.coverage.sse_broadcaster import SseBroadcaster

router = APIRouter(tags=["coverage"])


# Included in main.py under /api/v2. The path is a placeholder until the
# coverage stream contract is published.
@router.get("/coverage/stream", response_class=EventSourceResponse)
async def stream(request: Request) -> AsyncIterable[ServerSentEvent]:
    """Stream station coverage to one dashboard over SSE.

    1. Subscribe to the broadcaster to get this connection's queue.
    2. Send updater.snapshot() as the first event. No await between steps 1
       and 2, so no update is missed or sent twice.
    3. Wait on the queue and yield one ServerSentEvent per refresh, each
       carrying the full coverage, the same payload as the snapshot.
    4. When the client disconnects, unsubscribe (in a finally block).

    The updater and the broadcaster are taken from request.app.state.
    """
    broadcaster: SseBroadcaster = request.app.state.sse_broadcaster
    updater: CoverageUpdater = request.app.state.coverage_updater
    queue = broadcaster.subscribe()
    try:
        yield ServerSentEvent(data=updater.snapshot(), event="coverage")
        while True:
            coverage = await queue.get()
            yield ServerSentEvent(data=coverage, event="coverage")
    finally:
        broadcaster.unsubscribe(queue)
