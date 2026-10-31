from fastapi import APIRouter, Request, status

from src.api.v2.dependencies import EventProducerDep
from src.api.v2.schemas.ingestion import PatrolSessionEvent
from src.domain.event import EventType
from src.services.station_coverage.coverage_updater import CoverageUpdater
from src.services.train_manning.train_manning_updater import TrainManningUpdater

router = APIRouter(tags=["patrol-session"])


@router.post("/patrol-session/start", status_code=status.HTTP_201_CREATED)
async def patrol_session_start_event(
    patrol_session_event: PatrolSessionEvent,
    producer: EventProducerDep,
    request: Request,
):
    event = await producer.append_event(
        event_type=EventType.START_EVENT,
        android_id=patrol_session_event.android_id,
        device_timestamp=patrol_session_event.timestamp,
    )
    coverage_updater: CoverageUpdater = request.app.state.coverage_updater
    await coverage_updater.refresh()
    train_manning_updater: TrainManningUpdater = request.app.state.train_manning_updater
    await train_manning_updater.refresh()
    return event


@router.post("/patrol-session/stop", status_code=status.HTTP_201_CREATED)
async def patrol_session_stop_event(
    patrol_session_event: PatrolSessionEvent,
    producer: EventProducerDep,
    request: Request,
):
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
    train_manning_updater: TrainManningUpdater = request.app.state.train_manning_updater
    await train_manning_updater.refresh()
    return event
