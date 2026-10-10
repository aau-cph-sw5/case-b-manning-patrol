import json
from pathlib import Path
from uuid import UUID

from sqlmodel import delete
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models import PatrolArea, Station
from src.models.patrol_area import AreaKind
from src.models.line import Line
from src.models.station_line import StationLine

STATIONS_FILE = Path(__file__).parent.parent / "data" / "stations.v1.json"

async def load_stations(session: AsyncSession, path: Path = STATIONS_FILE) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))

    await session.exec(delete(StationLine))
    await session.exec(delete(PatrolArea))
    await session.exec(delete(Station))
    await session.exec(delete(Line))

    for station in data["stations"]:
        session.add(
            Station(id=station["id"], name=station["name"])
        )
        
    for line in data["lines"]:
        session.add(
            Line(id=line["id"], name=line["name"])
        )

    # create station-line relationships
    for station in data["stations"]:
        for line_id in station["line_ids"]:
            session.add(
                StationLine(station_id=station["id"], line_id=line_id)
            )
    
    # Stations must exist in the database before areas can point to them.
    await session.flush()

    for station in data["stations"]:
        for area in station["patrol_areas"]:
            session.add(
                PatrolArea(
                    beacon_id=UUID(area["beacon_id"]),
                    station_id=station["id"],
                    area_id=area["id"],
                    area_kind=AreaKind(area["kind"]),
                )
            )

    await session.commit()
