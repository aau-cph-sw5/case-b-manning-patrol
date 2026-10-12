from datetime import datetime

from pydantic import BaseModel, Field


class ConnectionEvent(BaseModel):
    """Ingestion payload for POST /connection/connect and /connection/disconnect
    (contracts/positioning-ingestion/v2). Which endpoint was called says whether
    the beacon was connected or disconnected; the payload does not carry it."""

    android_id: str = Field(..., min_length=1)
    beacon_id: str = Field(..., min_length=1)
    timestamp: datetime
