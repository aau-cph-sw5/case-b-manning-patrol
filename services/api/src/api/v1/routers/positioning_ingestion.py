"""
Positioning Ingestion

The Android app's ingestion endpoints, per contracts/positioning-ingestion/v1.
Each endpoint is exactly one action, so the payload carries no status field;
the server appends to the event log and answers 201.
"""

from fastapi import APIRouter, status

from services.api.src.models.beacon_to_station import ConnectionEvent, PatrolSessionEvent
from src.services.ingestion_service import record_connection_event, record_patrol_session_event

router = APIRouter(tags=["positioning-ingestion"])


@router.post("/connection/connect", status_code=status.HTTP_201_CREATED)
def report_connection_connect(event: ConnectionEvent) -> None:
    """Report that an android device connected to a beacon."""
    record_connection_event(event, action="CONNECTED")


@router.post("/connection/disconnect", status_code=status.HTTP_201_CREATED)
def report_connection_disconnect(event: ConnectionEvent) -> None:
    """Report that an android device disconnected from a beacon."""
    record_connection_event(event, action="DISCONNECTED")


@router.post("/patrol-session/start", status_code=status.HTTP_201_CREATED)
def report_patrol_session_start(event: PatrolSessionEvent) -> None:
    """Report that a steward started their patrol session."""
    record_patrol_session_event(event, action="PATROL_SESSION_STARTED")


@router.post("/patrol-session/stop", status_code=status.HTTP_201_CREATED)
def report_patrol_session_stop(event: PatrolSessionEvent) -> None:
    """Report that a steward stopped their patrol session."""
    record_patrol_session_event(event, action="PATROL_SESSION_STOPPED")
