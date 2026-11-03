"""Convert coverage reports into the dashboard payload sent to the web app."""

from datetime import datetime

from src.api.v2.schemas.trains import TrainsUpdate, TrainsUpdateTrain
from src.db.models import Station, StationLine
from src.domain.train_manning import TrainManningReport


class TrainsUpdatePresenter:
    def __init__(self, stations: list[Station], station_lines: list[StationLine]):
        self._names = {station.id: station.name for station in stations}
        lines: dict[str, list[str]] = {}
        for station_line in sorted(station_lines, key=lambda sl: sl.line_id):
            lines.setdefault(station_line.station_id, []).append(station_line.line_id)
        self._lines = lines

    def to_trains_update(
        self,
        train_reports: list[TrainManningReport],
        sent_at: datetime,
    ) -> TrainsUpdate:
        return TrainsUpdate(
            trains=[TrainsUpdatePresenter._train(report) for report in train_reports],
            time=sent_at,
        )

    @staticmethod
    def _train(report: TrainManningReport) -> TrainsUpdateTrain:
        return TrainsUpdateTrain(
            train_id=report.train.train_id,
            slug=report.train.slug,
            current_steward_ids=sorted(report.current_steward_ids),
            line=sorted(report.train.line_ids),
        )
