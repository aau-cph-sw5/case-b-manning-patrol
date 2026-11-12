"""Endpoint for a steward's patrol records in the current shift."""

import logging
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel.ext.asyncio.session import AsyncSession

from src.api.v2.dependencies import AsyncDbSessionDep
from src.api.v2.schemas.patrol_record import (
    AreaType,
    Record,
    RecordArea,
    RecordList,
    Status,
)
from src.authorization.dependencies import require_permission
from src.db.models.event import Event
from src.db.repository.event import (
    get_connection_events_by_android_id,
    get_latest_start_event,
)
from src.db.repository.patrol_area import get_patrol_areas
from src.db.repository.station import get_station_lines, get_stations
from src.domain.event import EventType
from src.domain.patrol_area import AreaKind
from src.security.current_user import User
from src.services.station_coverage.coverage_window import MIN_QUALIFYING_DURATIONS

logger = logging.getLogger(__name__)

router = APIRouter(tags=["patrol_record"])


class RecordBuildError(Exception):
    """The steward's records could not be built from the stored data."""


@router.get("/record")
async def get_records(
    android_id: UUID,
    session: AsyncDbSessionDep,
    user: Annotated[
        User, Depends(require_permission("presence.own.all_lines.current_shift"))
    ],
) -> RecordList:
    """Return the steward's patrol records for the current shift, most recent first.

    Raises RecordBuildError if the database cannot be read.
    """
    try:
        return await build_records(session, android_id)
    except SQLAlchemyError as error:
        raise RecordBuildError("Could not read the steward's patrol records") from error


async def build_records(session: AsyncSession, android_id: UUID) -> RecordList:
    """Pair the steward's shift connects and disconnects into records per beacon.

    A disconnect closes its beacon's open connect as a closed record; connects
    still open at the end become open records. Beacons without a patrol area are
    skipped.
    Returns the records sorted by start time, most recent first, or an empty list
    if the steward has not started a shift.
    """
    events: list[Event] = await get_shift_connection_events(session, android_id)
    areas: dict[UUID, RecordArea] = await get_record_areas(session)

    records: list[Record] = []
    open_connects: dict[UUID, Event] = {}
    now = datetime.now(UTC)
    for event in events:
        if event.beacon_id is None or event.beacon_id not in areas:
            continue
        if event.event_type == EventType.CONNECT_EVENT:
            open_connects[event.beacon_id] = event
            continue
        connect = open_connects.pop(event.beacon_id, None)
        if connect is not None:
            record = build_record(
                event.beacon_id, areas[event.beacon_id], connect, event, now
            )
            records.append(record)
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
    """Map each beacon to the area it belongs to, named after its station.

    Areas without a beacon or station are skipped, as are areas whose station is
    not stored, so one bad row does not break every steward's records.
    """
    stations = {station.id: station for station in await get_stations(session)}
    lines: dict[str, list[str]] = {}
    for station_line in await get_station_lines(session):
        lines.setdefault(station_line.station_id, []).append(station_line.line_id)

    areas: dict[UUID, RecordArea] = {}
    for area in await get_patrol_areas(session):
        if area.beacon_id is None or area.station_id is None:
            continue
        station = stations.get(area.station_id)
        if station is None:
            logger.warning(
                "Skipping patrol area %s: unknown station %s",
                area.area_id,
                area.station_id,
            )
            continue
        areas[area.beacon_id] = RecordArea(
            area_id=area.area_id,
            name=f"{station.name} {area.area_kind.value}",
            line=sorted(lines.get(area.station_id, [])),
            station_id=area.station_id,
            area_type=AreaType(area.area_kind.value),
        )
    return areas


def build_record(
    beacon_id: UUID,
    area: RecordArea,
    connect: Event,
    disconnect: Event | None,
    now: datetime,
) -> Record:
    """Build a closed record, or an open one measured up to `now`.

    `disconnect` is None for an open record. The area counts as patrolled once
    the visit lasts at least the minimum qualifying duration for its area type.
    """
    min_duration = MIN_QUALIFYING_DURATIONS[AreaKind(area.area_type.value)]
    ended_at = disconnect.device_timestamp if disconnect is not None else None
    effective_end = ended_at if ended_at is not None else now
    duration = effective_end - connect.device_timestamp
    return Record(
        android_id=connect.android_id,
        beacon_id=beacon_id,
        started_at=connect.device_timestamp,
        ended_at=ended_at,
        duration_secs=int(duration.total_seconds()),
        min_patrol_duration_secs=int(min_duration.total_seconds()),
        patrolled=duration >= min_duration,
        status=Status.CLOSED if ended_at is not None else Status.OPEN,
        area=area,
    )
