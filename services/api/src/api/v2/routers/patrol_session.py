"""Endpoints for the start and end of a steward's patrol session."""

from fastapi import APIRouter, Request, status

from src.api.v2.dependencies import EventProducerDep
from src.api.v2.schemas.ingestion import PatrolSessionEvent
from src.domain.event import EventType
from src.services.station_coverage.coverage_updater import CoverageUpdater

router = APIRouter(tags=["patrol-session"])


@router.post("/patrol-session/start", status_code=status.HTTP_201_CREATED)
async def patrol_session_start_event(
    patrol_session_event: PatrolSessionEvent,
    producer: EventProducerDep,
    request: Request,
):
    """Record that a steward started a patrol session.

    The event is stored for the record only: coverage is measured from the
    scheduled shift start, not from this event. Coverage is recalculated and
    pushed to the dashboard stream, and the stored event is returned.
    """
    event = await producer.append_event(
        event_type=EventType.START_EVENT,
        android_id=patrol_session_event.android_id,
        device_timestamp=patrol_session_event.timestamp,
    )
    coverage_updater: CoverageUpdater = request.app.state.coverage_updater
    await coverage_updater.refresh()
    return event


@router.post("/patrol-session/stop", status_code=status.HTTP_201_CREATED)
async def patrol_session_stop_event(
    patrol_session_event: PatrolSessionEvent,
    producer: EventProducerDep,
    request: Request,
):
    """Record that a steward ended a patrol session.

    Also stores a disconnect, at the stop time, for every beacon the steward
    is still connected to. Coverage is recalculated and pushed to the
    dashboard stream, and the stored stop event is returned.
    """
    event = await producer.append_event(
        event_type=EventType.STOP_EVENT,
        android_id=patrol_session_event.android_id,
        device_timestamp=patrol_session_event.timestamp,
    )
    await producer.close_open_connections(
        android_id=patrol_session_event.android_id,
        device_timestamp=patrol_session_event.timestamp,
    )
    coverage_updater: CoverageUpdater = request.app.state.coverage_updater
    await coverage_updater.refresh()
    return event
