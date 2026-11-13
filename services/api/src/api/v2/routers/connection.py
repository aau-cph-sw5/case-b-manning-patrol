"""Endpoints for beacon connect and disconnect events from steward phones."""

from fastapi import APIRouter, Depends, Request, status

from src.api.v2.dependencies import EventProducerDep
from src.api.v2.schemas.ingestion import ConnectionEvent
from src.authorization.dependencies import require_permission
from src.domain.event import EventType
from src.security.current_user import User
from src.services.station_coverage.coverage_updater import CoverageUpdater
from src.services.train_manning.train_manning_updater import TrainManningUpdater

router = APIRouter(tags=["connection"])


@router.post("/connection/connect", status_code=status.HTTP_201_CREATED)
async def connection_event(
    connection_event: ConnectionEvent, producer: EventProducerDep, request: Request, user: User = Depends(require_permission("steward_patrol_view"))
):
    """Record that a steward's phone connected to a beacon.

    Stores the event, recalculates station coverage and pushes it to the
    dashboard stream, then returns the stored event.
    """
    event = await producer.append_event(
        event_type=EventType.CONNECT_EVENT,
        android_id=connection_event.android_id,
        beacon_id=connection_event.beacon_id,
        device_timestamp=connection_event.timestamp,
    )
    coverage_updater: CoverageUpdater = request.app.state.coverage_updater
    await coverage_updater.refresh()
    train_manning_updater: TrainManningUpdater = request.app.state.train_manning_updater
    await train_manning_updater.refresh()
    return event


@router.post("/connection/disconnect", status_code=status.HTTP_201_CREATED)
async def disconnection_event(
    connection_event: ConnectionEvent, producer: EventProducerDep, request: Request
):
    """Record that a steward's phone lost its connection to a beacon.

    Stores the event, recalculates station coverage and pushes it to the
    dashboard stream, then returns the stored event.
    """
    event = await producer.append_event(
        event_type=EventType.DISCONNECT_EVENT,
        android_id=connection_event.android_id,
        beacon_id=connection_event.beacon_id,
        device_timestamp=connection_event.timestamp,
    )
    coverage_updater: CoverageUpdater = request.app.state.coverage_updater
    await coverage_updater.refresh()
    train_manning_updater: TrainManningUpdater = request.app.state.train_manning_updater
    await train_manning_updater.refresh()
    return event
