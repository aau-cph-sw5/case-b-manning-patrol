
from datetime import datetime


class AtRiskCount(BaseModel):
    """At-risk episodes counted for one shift."""

    shift_start: datetime
    episodes: int