from datetime import datetime

from pydantic import BaseModel, Field


class PatrolSessionEvent(BaseModel):
    """Ingestion payload for POST /patrolSession/start and /patrolSession/stop
    (contracts/positioning-ingestion/v2)."""
    id: str = Field(..., min_length=1)
    timestamp: datetime