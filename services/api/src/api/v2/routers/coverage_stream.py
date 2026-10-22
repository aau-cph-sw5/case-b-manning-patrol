from collections.abc import AsyncIterable
from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.sse import EventSourceResponse, ServerSentEvent

from src.models.coverage import AreaCoverageReport, StationCoverageReport
from src.services.coverage.coverage_updater import CoverageUpdater
from src.services.coverage.sse_broadcaster import SseBroadcaster

router = APIRouter(tags=["coverage"])


# Included in main.py under /api/v2. The stream is specified by the
# coverage-stream contract; every event carries the full coverage.
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
        yield ServerSentEvent(
            data=_coverage_payload(updater.snapshot()), event="coverage"
        )
        while True:
            coverage = await queue.get()
            yield ServerSentEvent(data=_coverage_payload(coverage), event="coverage")
    finally:
        broadcaster.unsubscribe(queue)


def _coverage_payload(reports: list[StationCoverageReport]) -> list[dict]:
    """The coverage as the contract defines it: one entry per station.

    Every event carries the full coverage, so a client always replaces its
    whole state instead of merging.
    """
    return [_station_payload(report) for report in reports]


def _station_payload(report: StationCoverageReport) -> dict:
    return {
        "station_id": report.station_id,
        "status": report.coverage_status.value,
        "areas": [_area_payload(area) for area in report.areas],
    }


def _area_payload(area: AreaCoverageReport) -> dict:
    return {
        "area_id": area.area.area_id,
        "type": area.area.kind.value,
        "covered_now": area.covered_now,
        "stewards_present": sorted(
            str(steward_id) for steward_id in area.current_steward_ids
        ),
        "last_covered_at": _isoformat(area.last_covered_at),
        "status": area.coverage_status.value,
        "overdue_at": _isoformat(area.overdue_at),
        "as_of": area.as_of.isoformat(),
    }


def _isoformat(moment: datetime | None) -> str | None:
    return moment.isoformat() if moment is not None else None
