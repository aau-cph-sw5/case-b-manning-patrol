from uuid import UUID

from pydantic import BaseModel, Field


class BeaconToStation(BaseModel):
    beacon_id: UUID = Field(..., alias="Id")
    station: str | None = Field(None, alias="Station")
    train: str | None = Field(None, alias="Train")
