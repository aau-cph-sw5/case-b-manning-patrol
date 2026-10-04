import uuid
from uuid import UUID
from pydantic import BaseModel
from sqlmodel import SQLModel, Field
from datetime import datetime
from sqlalchemy import DateTime
from enum import Enum

# Event ingestion has 3 parts:

# 1. BaseModel:
#    Defines the JSON payload shape for the API.

# 2. API Endpoint logic:
#    Receives the BaseModel and decides the event type.

# 3. SQLModel:
#    Defines the database table and stores the parsed data.



class EventType(str, Enum):
    CONNECT = "ConnectionEvent"
    DISCONNECT = "DisconnectionEvent"
    ADJUST = "AdjustmentEvent"

# 1. BaseModels, receives json payload
class BeaconToStation(BaseModel):
    beacon_id: UUID = Field(..., alias="Id")
    station: str | None = Field(None, alias="Station")
    train: str | None = Field(None, alias="Train")

class ConnectionEvent(BaseModel):
    beacon_id: UUID
    android_id: UUID
    timestamp: datetime

# 3. SQLModels, defines database tables
class EventStore(SQLModel, table=True):
    event_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    event_type: EventType
    timestamp: datetime = Field(sa_type=DateTime)
    beacon_id: UUID = Field(foreign_key="datasheet.beacon_id")
    android_id: UUID

class Datasheet(SQLModel, table=True):
    beacon_id: UUID = Field(primary_key=True)
    station: str
    concourse: bool
    platform: bool