from uuid import UUID

from pydantic import AwareDatetime, BaseModel


class ConnectionEvent(BaseModel):
    android_id: UUID
    beacon_id: UUID
    timestamp: AwareDatetime


class PatrolSessionEvent(BaseModel):
    android_id: UUID
    timestamp: AwareDatetime
