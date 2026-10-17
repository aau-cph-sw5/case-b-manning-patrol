from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CoveredTimeSpan:
    start: datetime
    end: datetime

    def touches(self, other: CoveredTimeSpan) -> bool:
        """Tell whether this span and another can be merged into one.

        True when they overlap, or when one ends exactly where the other starts.
        Touching spans leave no uncovered moment between them, so the area was
        never overdue there. CoverageWindow._union checks this before merge.
        """
        if self.end < other.start:
            return False
        if other.end < self.start:
            return False
        return True

    def merge(self, other: CoveredTimeSpan) -> CoveredTimeSpan:
        """Combine two touching spans into one.

        Returns a span from the earlier start to the later end. Only call it
        when touches(other) is True: for spans with a gap between them, the
        result would wrongly cover the gap.
        """
        if not self.touches(other):
            raise ValueError("Cannot merge non-touching spans")
        return CoveredTimeSpan(
            start=min(self.start, other.start), end=max(self.end, other.end)
        )
