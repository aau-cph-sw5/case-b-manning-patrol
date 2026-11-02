from fastapi import APIRouter, Request, status

from src.api.v2.dependencies import EventProducerDep
from src.api.v2.schemas.ingestion import ConnectionEvent
from src.domain.event import EventType
from src.services.station_coverage.coverage_updater import CoverageUpdater

router = APIRouter(tags=["connection"])


@router.post("/connection/connect", status_code=status.HTTP_201_CREATED)
async def connection_event(
    connection_event: ConnectionEvent, producer: EventProducerDep, request: Request
):
    event = await producer.append_event(
        event_type=EventType.CONNECT_EVENT,
        android_id=connection_event.android_id,
        beacon_id=connection_event.beacon_id,
        device_timestamp=connection_event.timestamp,
    )
    coverage_updater: CoverageUpdater = request.app.state.coverage_updater
    await coverage_updater.refresh()
    return event


@router.post("/connection/disconnect", status_code=status.HTTP_201_CREATED)
async def disconnection_event(
    connection_event: ConnectionEvent, producer: EventProducerDep, request: Request
):
    event = await producer.append_event(
        event_type=EventType.DISCONNECT_EVENT,
        android_id=connection_event.android_id,
        beacon_id=connection_event.beacon_id,
        device_timestamp=connection_event.timestamp,
    )
    coverage_updater: CoverageUpdater = request.app.state.coverage_updater
    await coverage_updater.refresh()
    return event
