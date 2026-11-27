"""Historical compliance report of one shift, rebuilt from the stored record.

Mounted in main.py under /api/v2; the endpoint is specified by the report
contract (contracts/api/v2/report)."""

from datetime import UTC, date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from src.api.v2.dependencies import AsyncDbSessionDep
from src.api.v2.schemas.report import ReportData
from src.authorization.dependencies import require_permission
from src.db.repository.station import get_station_lines, get_stations
from src.security.current_user import User
from src.services.compliance.reconstruction import ComplianceReconstructor
from src.services.report.report_presenter import ReportPresenter

router = APIRouter(tags=["report-data"])

DateQuery = Annotated[
    date,
    Query(
        alias="date",
        description="Local date the shift starts on, e.g. 2026-05-30.",
    ),
]
KnownAtQuery = Annotated[
    datetime | None,
    Query(
        description=(
            "ISO 8601 with offset; only events the backend had received by "
            "then count. Defaults to every stored event."
        )
    ),
]


class ReportNotAvailableError(Exception):
    """The requested shift cannot be reported on with the given parameters."""


@router.get("/report_data", response_model=ReportData)
async def get_report_data(
    request: Request,
    session: AsyncDbSessionDep,
    user: Annotated[User, Depends(require_permission("historical_data"))],
    day: DateQuery,
    known_at: KnownAtQuery = None,
) -> ReportData:
    """Return the compliance report of the shift that starts on ``date``.

    Rebuilds station coverage and train manning from the stored event log,
    evaluated at the shift end, or earlier when ``known_at`` is given, and
    resolves station names and lines for the report. ``known_at`` must carry
    a timezone offset. Raises ReportNotAvailableError when the shift had not
    started by now or by ``known_at``, or when ``known_at`` has no offset.
    """
    if known_at is not None and known_at.tzinfo is None:
        raise ReportNotAvailableError("known_at must include a timezone offset")
    reconstructor: ComplianceReconstructor = request.app.state.compliance_reconstructor
    try:
        compliance_picture = await reconstructor.reconstruct(
            session, day, current_time=datetime.now(UTC), known_at=known_at
        )
    except ValueError as error:
        raise ReportNotAvailableError(str(error)) from error
    presenter = ReportPresenter(
        await get_stations(session), await get_station_lines(session)
    )
    return presenter.to_report(compliance_picture)
