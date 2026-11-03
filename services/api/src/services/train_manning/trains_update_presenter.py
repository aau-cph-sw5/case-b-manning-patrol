"""Convert coverage reports into the dashboard payload sent to the web app."""

from datetime import datetime

from src.api.v2.schemas.trains import TrainsUpdate, TrainsUpdateTrain
from src.db.models.train import Train
from src.db.models.train_line import TrainLine
from src.domain.train_manning import TrainManningReport


class TrainsUpdatePresenter:
    def __init__(self, trains: list[Train], train_lines: list[TrainLine]):
        self._names = {train.id: train.name for train in trains}
        lines: dict[str, list[str]] = {}
        for train_line in sorted(train_lines, key=lambda sl: sl.line_id):
            lines.setdefault(train_line.train_id, []).append(train_line.line_id)
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
