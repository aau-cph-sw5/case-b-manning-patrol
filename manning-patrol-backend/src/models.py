from typing import Optional
from pydantic import BaseModel, Field

class BeaconToStation(BaseModel):
    beacon_id: str = Field(..., alias="Id")
    station: Optional[str] = Field(None,alias="Station")
    train: Optional[str] = Field(None, alias="Train")