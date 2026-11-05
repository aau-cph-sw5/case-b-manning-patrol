"""Build the trains stream payload sent to the web app."""

from datetime import datetime
from uuid import UUID

from src.api.v2.schemas.trains import TrainsUpdate, TrainsUpdateTrain
from src.db.models.train import Train
from src.db.models.train_line import TrainLine
from src.domain.train_manning import TrainManningReport


class TrainsUpdatePresenter:
    """Build the ``TrainsUpdate`` stream payload from train manning reports."""

    def __init__(self, trains: list[Train], train_lines: list[TrainLine]):
        self._names = {train.train_id: train.slug for train in trains}
        lines: dict[UUID, list[str]] = {}
        for train_line in sorted(train_lines, key=lambda sl: sl.line_id):
            lines.setdefault(train_line.train_id, []).append(train_line.line_id)
        self._lines = lines

    def to_trains_update(
        self,
        train_reports: list[TrainManningReport],
        sent_at: datetime,
    ) -> TrainsUpdate:
        """Build the ``TrainsUpdate`` for ``train_reports``, stamped with ``sent_at``.

        The manning percentages are the manned-time share of the running
        time (0-100) over all trains and over the M1/M2 and M3/M4 line
        groups separately; a group with no running time gets 0.
        """
        total_time = 0
        total_manning_time = 0

        m1m2_total_time = 0
        m1m2_total_manning_time = 0
        m3m4_total_time = 0
        m3m4_total_manning_time = 0

        for report in train_reports:
            if report.train.line_ids.intersection({"M1", "M2"}):
                m1m2_total_time += report.running_time.total_seconds()
                m1m2_total_manning_time += report.manned_time.total_seconds()
            if report.train.line_ids.intersection({"M3", "M4"}):
                m3m4_total_time += report.running_time.total_seconds()
                m3m4_total_manning_time += report.manned_time.total_seconds()
            total_time += report.running_time.total_seconds()
            total_manning_time += report.manned_time.total_seconds()

        total_manning_percent = (
            total_manning_time / total_time * 100 if total_time > 0 else 0
        )
        m1m2_manning_percent = (
            m1m2_total_manning_time / m1m2_total_time * 100
            if m1m2_total_time > 0
            else 0
        )
        m3m4_manning_percent = (
            m3m4_total_manning_time / m3m4_total_time * 100
            if m3m4_total_time > 0
            else 0
        )
        return TrainsUpdate(
            manning_percent=total_manning_percent,
            m1m2_manning_percent=m1m2_manning_percent,
            m3m4_manning_percent=m3m4_manning_percent,
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
