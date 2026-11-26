"""Server-sent events stream of train manning."""

from collections.abc import AsyncIterable
from contextlib import aclosing
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.sse import EventSourceResponse, ServerSentEvent

from src.authorization.dependencies import require_permission
from src.security.current_user import User
from src.services.train_manning.sse_broadcaster import SseTrainManningBroadcaster
from src.services.train_manning.sse_train_stream import SSETrainStream
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
    async with aclosing(stream.run_stream()) as events:
        async for event in events:
            yield event
