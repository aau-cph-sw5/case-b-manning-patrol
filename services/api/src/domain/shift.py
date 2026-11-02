"""A single scheduled shift."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Shift:
    """One concrete scheduled shift, with timezone-aware start and end."""

    start: datetime
    end: datetime
