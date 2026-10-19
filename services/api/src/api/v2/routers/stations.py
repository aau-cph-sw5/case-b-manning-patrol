from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.main import get_session
from src.models.patrol_area import PatrolArea
from src.models.station import Station

router = APIRouter(tags=["stations"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]


class AreaOut(BaseModel):
    kind: str
    beacon_id: UUID


class StationOut(BaseModel):
    name: str
    patrol_areas: list[AreaOut]


@router.get("/stations", response_model=list[StationOut])
async def list_stations(session: SessionDep):
    stations = (await session.exec(select(Station))).all()
    areas = (await session.exec(select(PatrolArea))).all()

    by_station: dict[str | None, list[PatrolArea]] = {}
    for area in areas:
        by_station.setdefault(area.station_id, []).append(area)

    return [
        StationOut(
            name=station.name,
            patrol_areas=[
                AreaOut(kind=area.area_kind.value, beacon_id=area.beacon_id)
                for area in by_station.get(station.id, [])
                if area.beacon_id is not None
            ],
        )
        for station in stations
    ]
