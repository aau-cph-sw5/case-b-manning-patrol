"""The compliance picture of one shift, as rebuilt from the stored record."""

from dataclasses import dataclass
from datetime import datetime

from src.domain.coverage import StationCoverageReport
from src.domain.shift import Shift
from src.domain.train_manning import TrainManningReport


@dataclass(frozen=True)
class CompliancePicture:
    """Station coverage and train manning for one shift at one point in time.

    ``as_of`` is the moment the reports are evaluated at: the shift end, or
    earlier when the shift was still running at ``known_at`` or at the time
    of the request. ``known_at`` is the server-time cutoff the reports were
    built with; None means every stored event was used.
    """

    shift: Shift
    as_of: datetime
    known_at: datetime | None
    stations: tuple[StationCoverageReport, ...]
    trains: tuple[TrainManningReport, ...]
