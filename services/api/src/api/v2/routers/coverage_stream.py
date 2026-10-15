from collections.abc import AsyncIterable

from fastapi import APIRouter, Request
from fastapi.sse import EventSourceResponse, ServerSentEvent

router = APIRouter(tags=["coverage"])


# Not included in main.py yet. The path is a placeholder: no contract defines it.
@router.get("/coverage/stream", response_class=EventSourceResponse)
async def stream(request: Request) -> AsyncIterable[ServerSentEvent]:
    """Stream station coverage to one dashboard over SSE.

    1. Subscribe to the broadcaster to get this connection's queue.
    2. Send updater.snapshot() as the first event. No await between steps 1 and
       2, so no update is missed or sent twice.
    3. Wait on the queue and yield one ServerSentEvent per changed station.
    4. When the client disconnects, unsubscribe (in a finally block).

    The updater and the broadcaster are taken from request.app.state.
    """
    raise NotImplementedError
    # FastAPI only treats an async generator as an SSE stream.
    yield
