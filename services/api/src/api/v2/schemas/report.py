"""Response payload of the historical compliance report endpoint.

Defined by the positioning-interface contract.
"""

from datetime import datetime, timedelta
from uuid import UUID

from pydantic import BaseModel, field_serializer

from src.domain.coverage import CoverageStatus
from src.domain.patrol_area import AreaKind


class ShiftBoundary(BaseModel):
    """The scheduled start and end of the reported shift, in UTC."""

    start: datetime
    end: datetime


class ReportArea(BaseModel):
    """One patrol area in the report.

    `overdue_at` is when the area became overdue, or None while it is covered
    or was never covered. `last_covered_at` is None when no qualifying visit
    has finished.
    """

    area_id: str
    name: str
    line: list[str]
    area_type: AreaKind
    covered_now: bool
    overdue_at: datetime | None
    last_covered_at: datetime | None
    coverage_status: CoverageStatus


class ReportStation(BaseModel):
    """A station, its lines, and its patrol areas in the report."""

    station_id: str
    name: str
    line: list[str]
    areas: list[ReportArea]


class ReportTrain(BaseModel):
    """One train's manning over the reported shift.

    `manned_ratio` is manned time over running time, or None when the train
    had no running time. The durations serialize as seconds in JSON.
    """

    train_id: UUID
    slug: str
    line: list[str]
    manned_ratio: float | None
    manned_now: bool
    manned_time: timedelta
    running_time: timedelta

    @field_serializer("manned_time", "running_time")
    def _serialize_duration(self, value: timedelta) -> float:
        """Serialize durations as seconds in JSON."""
        return value.total_seconds()


class ReportData(BaseModel):
    """The compliance report of one shift, evaluated at `as_of`.

    `known_at` is the server-time cutoff the report was built with, or None
    when every stored event was used. The percentages are the manned-time
    share (0-100) over all trains and over the M1/M2 and M3/M4 line groups;
    None when the scope had no running time.
    """

    shift: ShiftBoundary
    as_of: datetime
    known_at: datetime | None = None
    stations: list[ReportStation]
    trains: list[ReportTrain]
    manning_percent: float | None
    m1m2_manning_percent: float | None
    m3m4_manning_percent: float | None
