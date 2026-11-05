"""Load station and train reference data into the database."""

import json
from pathlib import Path
from uuid import UUID

from sqlmodel import delete
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models import Line, PatrolArea, Station, StationLine, Train, TrainLine
from src.domain.patrol_area import AreaKind

STATIONS_FILE = Path(__file__).parent.parent / "data" / "stations.v1.json"
TRAINS_FILE = Path(__file__).parent.parent / "data" / "trains.v1.json"


async def load_stations(session: AsyncSession, path: Path = STATIONS_FILE) -> None:
    """Replace all stations, lines and patrol areas with the contents of ``path``.

    Existing rows are deleted first, so the file is the single source of
    truth. Train-line links are cleared too, because they reference the lines
    being replaced; run ``load_trains`` afterwards to restore them. Commits
    when done.
    """
    data = json.loads(path.read_text(encoding="utf-8"))

    await session.exec(delete(TrainLine))
    await session.exec(delete(StationLine))
    await session.exec(delete(PatrolArea))
    await session.exec(delete(Station))
    await session.exec(delete(Line))

    for station in data["stations"]:
        session.add(Station(id=station["id"], name=station["name"]))

    for line in data["lines"]:
        session.add(Line(id=line["id"], name=line["name"]))

    for station in data["stations"]:
        for line_id in station["line_ids"]:
            session.add(StationLine(station_id=station["id"], line_id=line_id))

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


async def load_trains(session: AsyncSession, path: Path = TRAINS_FILE) -> None:
    """Replace all trains and their line links with the contents of ``path``.

    Existing rows are deleted first, so the file is the single source of
    truth. Every ``line_ids`` entry must exist in the ``line`` table, so run
    ``load_stations`` first. Commits when done.
    """
    data = json.loads(path.read_text(encoding="utf-8"))

    await session.exec(delete(TrainLine))
    await session.exec(delete(Train))

    for train in data["trains"]:
        session.add(
            Train(
                train_id=UUID(train["id"]),
                slug=train["slug"],
                beacon_id=UUID(train["beacon_id"]),
            )
        )

    # Trains must exist in the database before their line links can point to them.
    await session.flush()

    for train in data["trains"]:
        for line_id in train["line_ids"]:
            session.add(TrainLine(train_id=UUID(train["id"]), line_id=line_id))

    await session.commit()


async def load_reference_data(session: AsyncSession) -> None:
    """Replace stations and trains with the contents of the default data files.

    Stations are loaded first: ``load_stations`` replaces the lines that trains
    point to and clears the train-line links, which ``load_trains`` restores.
    Use this instead of calling either loader on its own. Commits after each
    file.
    """
    await load_stations(session)
    await load_trains(session)
