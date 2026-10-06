from datetime import datetime

from pydantic import BaseModel, Field


class BeaconToStation(BaseModel):
    beacon_id: str = Field(..., alias="Id")
    station: str | None = Field(None, alias="Station")
    train: str | None = Field(None, alias="Train")


class ConnectionEvent(BaseModel):
    """Ingestion payload for POST /connection/connect and /connection/disconnect
    (contracts/positioning-ingestion/v1). Which endpoint was called says whether
    the beacon was connected or disconnected; the payload does not carry it."""

    android_id: str = Field(..., min_length=1)
    beacon_id: str = Field(..., min_length=1)
    timestamp: datetime


class PatrolSessionEvent(BaseModel):
    """Ingestion payload for POST /patrolSession/start and /patrolSession/stop
    (contracts/positioning-ingestion/v1)."""

    id: str = Field(..., min_length=1)
