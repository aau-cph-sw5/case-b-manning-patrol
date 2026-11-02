"""Request bodies sent by the steward app."""

from uuid import UUID

from pydantic import AwareDatetime, BaseModel


class ConnectionEvent(BaseModel):
    """A phone connecting to or leaving a beacon; `timestamp` is device time."""

    android_id: UUID
    beacon_id: UUID
    timestamp: AwareDatetime


class PatrolSessionEvent(BaseModel):
    """A steward starting or ending a patrol; `timestamp` is device time."""

    android_id: UUID
    timestamp: AwareDatetime
