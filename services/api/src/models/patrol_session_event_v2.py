from datetime import datetime

from pydantic import BaseModel, Field


class PatrolSessionEventV2(BaseModel):
    """Timestamped v2 ingestion payload for patrol-session actions."""

    android_id: str = Field(..., min_length=1)
    timestamp: datetime
