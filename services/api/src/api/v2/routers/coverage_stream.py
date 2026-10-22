from collections.abc import AsyncIterable
from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.sse import EventSourceResponse, ServerSentEvent

from src.models.coverage import AreaCoverageReport, StationCoverageReport
from src.services.coverage.coverage_updater import CoverageUpdater
from src.services.coverage.sse_broadcaster import SseBroadcaster

router = APIRouter(tags=["coverage"])


@router.get("/coverage/stream", response_class=EventSourceResponse)
async def stream(request: Request) -> AsyncIterable[ServerSentEvent]:
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
