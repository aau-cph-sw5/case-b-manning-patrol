"""
Payload of the dashboard stream, as defined by the positioning-interface contract
(contracts/api/v2/positioning-interface)
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from src.models.patrol_area import AreaKind


class DashboardArea(BaseModel):
    area_id: str
    name: str
    line: str
    area_type: AreaKind
    covered_now: bool
    overdue_at: datetime | None


class DashboardStation(BaseModel):
    station_id: str
    name: str
    areas: list[DashboardArea]


class Train(BaseModel):
    train_id: UUID
    slug: str
    total_time_secs: int
    manned_time_secs: int
    current_steward_id: UUID | None


class Dashboard(BaseModel):
    stations: list[DashboardStation]
    trains: list[Train]
    time: datetime
