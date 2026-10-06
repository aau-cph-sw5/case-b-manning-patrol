import json
from pathlib import Path
from uuid import UUID

from sqlmodel import delete
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models import PatrolArea, Station
from src.models.patrol_area import AreaKind

STATIONS_FILE = Path(__file__).parent.parent / "data" / "stations.v1.json"


async def load_stations(session: AsyncSession, path: Path = STATIONS_FILE) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))

    await session.exec(delete(PatrolArea))
    await session.exec(delete(Station))

    for entry in data["stations"]:
        session.add(
            Station(id=entry["id"], name=entry["name"], line_ids=entry["line_ids"])
        )
    # Stations must exist in the database before areas can point to them.
    await session.flush()

    for entry in data["stations"]:
        for area in entry["patrol_areas"]:
            session.add(
                PatrolArea(
                    beacon_id=UUID(area["beacon_id"]),
                    station_id=entry["id"],
                    id=area["id"],
                    area_kind=AreaKind(area["kind"]),
                )
            )

    await session.commit()
