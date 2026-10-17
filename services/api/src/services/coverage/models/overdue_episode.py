# A stretch of time an area went without qualifying coverage. cleared_at is None
# while it is still overdue.
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class OverdueEpisode:
    overdue_at: datetime
    cleared_at: datetime | None

    def is_open(self) -> bool:
        """Tell whether the area is still overdue.

        True when no qualifying visit has ended the episode yet, which means
        cleared_at is None.
        """
        if self.cleared_at is None:
            return True
        return False

    def duration(self, now: datetime) -> timedelta:
        """How long the area has been, or was, overdue.

        cleared_at - overdue_at for a cleared episode, now - overdue_at for an
        open one. now is a parameter, so the result is repeatable.
        """
        if self.cleared_at is not None:
            return self.cleared_at - self.overdue_at
        return now - self.overdue_at
