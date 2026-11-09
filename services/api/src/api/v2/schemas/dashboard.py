"""Payload of the dashboard stream.

Defined by the positioning-interface contract
(contracts/api/v2/positioning-interface).
"""

from datetime import datetime

from pydantic import BaseModel

from src.domain.patrol_area import AreaKind


class DashboardArea(BaseModel):
    """One patrol area on the dashboard.

    `overdue_at` is when the area becomes overdue, or None while it is covered.
    """

    area_id: str
    name: str
    line: list[str]
    area_type: AreaKind
    covered_now: bool
    overdue_at: datetime | None


class DashboardStation(BaseModel):
    """A station and its patrol areas."""

    station_id: str
    name: str
    areas: list[DashboardArea]


class Dashboard(BaseModel):
    """The full dashboard sent on every stream event; `time` is when it was sent."""

    stations: list[DashboardStation]
    time: datetime
