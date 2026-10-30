"""The daily shift schedule that coverage is measured against."""

import json
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from src.domain.shift import Shift

SHIFTS_FILE = Path(__file__).parents[2] / "data" / "shifts.v1.json"


class ShiftSchedule:
    """A shift that repeats every day at the same local start and end time.

    An end time earlier than the start time means the shift runs past
    midnight and ends the next day.
    """

    def __init__(self, start: time, end: time, timezone: ZoneInfo) -> None:
        if start == end:
            raise ValueError("A shift must start and end at different times")
        self._start = start
        self._end = end
        self._timezone = timezone

    @classmethod
    def from_file(cls, path: Path = SHIFTS_FILE) -> "ShiftSchedule":
        """Load the night shift and its timezone from the shifts JSON file."""
        data = json.loads(path.read_text(encoding="utf-8"))
        night_shift = data["night_shift"]
        return cls(
            start=time.fromisoformat(night_shift["start"]),
            end=time.fromisoformat(night_shift["end"]),
            timezone=ZoneInfo(data["timezone"]),
        )

    def latest_shift(self, now: datetime) -> Shift:
        """Return the most recent shift that started at or before ``now``.

        The shift may already have ended; callers compare ``now`` with
        ``Shift.end`` themselves. ``now`` must be timezone-aware, and the
        returned start and end are in UTC.
        """
        today = now.astimezone(self._timezone).date()
        shift = self._shift_starting_on(today)
        if shift.start > now:
            shift = self._shift_starting_on(today - timedelta(days=1))
        return shift

    def _shift_starting_on(self, day: date) -> Shift:
        end_day = day if self._end > self._start else day + timedelta(days=1)
        start = datetime.combine(day, self._start, tzinfo=self._timezone)
        end = datetime.combine(end_day, self._end, tzinfo=self._timezone)
        return Shift(start=start.astimezone(UTC), end=end.astimezone(UTC))
