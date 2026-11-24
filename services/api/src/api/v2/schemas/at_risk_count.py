
from datetime import datetime
from pydantic import BaseModel

class AtRiskCount(BaseModel):
    """At-risk episodes counted for one shift."""

    shift_start: datetime
    episodes: int