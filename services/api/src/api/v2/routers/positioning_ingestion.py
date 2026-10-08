"""Timestamped v2 ingestion endpoints used by the Android demo."""

from fastapi import APIRouter, status

from src.models.connection_event import ConnectionEvent
from src.models.patrol_session_event_v2 import PatrolSessionEventV2
from src.services.ingestion_service import (
    record_connection_event,
    record_patrol_session_event_v2,
)

router = APIRouter(tags=["positioning-ingestion-v2"])


@router.post("/connection/connect", status_code=status.HTTP_201_CREATED)
def report_connection_connect(event: ConnectionEvent) -> None:
    record_connection_event(event, action="CONNECTED")


@router.post("/connection/disconnect", status_code=status.HTTP_201_CREATED)
def report_connection_disconnect(event: ConnectionEvent) -> None:
    record_connection_event(event, action="DISCONNECTED")


@router.post("/patrol-session/start", status_code=status.HTTP_201_CREATED)
def report_patrol_session_start(event: PatrolSessionEventV2) -> None:
    record_patrol_session_event_v2(event, action="PATROL_SESSION_STARTED")


@router.post("/patrol-session/stop", status_code=status.HTTP_201_CREATED)
def report_patrol_session_stop(event: PatrolSessionEventV2) -> None:
    record_patrol_session_event_v2(event, action="PATROL_SESSION_STOPPED")
