from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter
from sqlmodel.ext.asyncio.session import AsyncSession

from src.api.v2.dependencies import AsyncDbSessionDep
from src.api.v2.schemas.patrol_record import (
    AreaType,
    Record,
    RecordArea,
    RecordList,
    Status,
)
from src.db.models.event import Event
from src.db.repository.event import (
    get_connection_events_by_android_id,
    get_latest_start_event,
)
from src.db.repository.patrol_area import get_patrol_areas
from src.db.repository.station import get_station_lines, get_stations
from src.domain.event import EventType
from src.domain.patrol_area import AreaKind
from src.services.station_coverage.coverage_window import MIN_QUALIFYING_DURATIONS

router = APIRouter(tags=["patrol_record"])


@router.get("/record")
async def get_records(android_id: UUID, session: AsyncDbSessionDep) -> RecordList:
    """Return the steward's patrol records for the current shift, most recent first."""
    # This endpoint needs some error handling such as
    # Custom errors, HTTP exceptions etc
    return await build_records(session, android_id)


async def build_records(session: AsyncSession, android_id: UUID) -> RecordList:
    """Pair the steward's shift connects and disconnects into records per beacon.

    A disconnect closes its beacon's open connect as a registered record; connects
    still open at the end become pending. Beacons without a patrol area are skipped.

    Returns: RecordList sorted [latest, ..., earliest] for one android_id
    """
    now = datetime.now(UTC)
    events: list[Event] = await get_shift_connection_events(session, android_id)
    areas: dict[UUID, RecordArea] = await get_record_areas(session)

    records: list[Record] = []
    open_connects: dict[UUID, Event] = {}
    for event in events:
        if event.beacon_id is None or event.beacon_id not in areas:
            continue
        if event.event_type == EventType.CONNECT_EVENT:
            open_connects[event.beacon_id] = event
        # I think this is gonna work but we may need to talk about it.
        # Since a disconnection event should not be sent without an earlier
        # connection event it should work
        elif (connect := open_connects.pop(event.beacon_id, None)) is not None:
            records.append(
                build_record(
                    event.beacon_id, areas[event.beacon_id], connect, event, now
                )
            )
    for beacon_id, connect in open_connects.items():
        records.append(build_record(beacon_id, areas[beacon_id], connect, None, now))

    records.sort(key=lambda record: record.started_at, reverse=True)
    return RecordList(records=records, time=now)


async def get_shift_connection_events(
    session: AsyncSession, android_id: UUID
) -> list[Event]:
    """Return the steward's connection events since their latest shift start."""
    latest_shift_start = await get_latest_start_event(session, android_id)
    if latest_shift_start is None:
        return []
    return await get_connection_events_by_android_id(
        session, android_id, latest_shift_start.device_timestamp
    )


async def get_record_areas(session: AsyncSession) -> dict[UUID, RecordArea]:
    """Map each beacon to the area it belongs to, named after its station."""
    stations = {station.id: station for station in await get_stations(session)}
    lines: dict[str, list[str]] = {}
    for station_line in await get_station_lines(session):
        lines.setdefault(station_line.station_id, []).append(station_line.line_id)

    return {
        area.beacon_id: RecordArea(
            area_id=area.area_id,
            name=f"{stations[area.station_id].name} {area.area_kind.value}",
            line=sorted(lines.get(area.station_id, [])),
            station_id=area.station_id,
            area_type=AreaType(area.area_kind.value),
        )
        for area in await get_patrol_areas(session)
        if area.beacon_id is not None and area.station_id is not None
    }


def build_record(
    beacon_id: UUID,
    area: RecordArea,
    connect: Event,
    disconnect: Event | None,
    now: datetime,
) -> Record:
    """Build a registered record, or a pending one measured up to `now`."""
    min_duration = MIN_QUALIFYING_DURATIONS[AreaKind(area.area_type.value)]
    ended_at = disconnect.device_timestamp if disconnect is not None else None
    duration = (ended_at or now) - connect.device_timestamp

    return Record(
        android_id=connect.android_id,
        beacon_id=beacon_id,
        started_at=connect.device_timestamp,
        ended_at=ended_at,
        duration_secs=int(duration.total_seconds()) if ended_at else None,
        min_patrol_duration_secs=int(min_duration.total_seconds()),
        patrolled=duration >= min_duration,
        status=Status.REGISTERED if ended_at else Status.PENDING,
        area=area,
    )
