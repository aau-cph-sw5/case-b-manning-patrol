"""
Positioning Ingestion

The Android app's ingestion endpoints, per contracts/positioning-ingestion/v1.
Each endpoint is exactly one action, so the payload carries no status field;
the server appends to the event log and answers 201.
"""

from fastapi import APIRouter, status

from src.models import ConnectionEvent, ShiftEvent
from src.services.ingestion_service import record_connection_event, record_shift_event

router = APIRouter(tags=["positioning-ingestion"])


@router.post("/connection/connect", status_code=status.HTTP_201_CREATED)
def report_connection_connect(event: ConnectionEvent) -> None:
    """Report that an android device connected to a beacon."""
    record_connection_event(event, action="CONNECTED")


@router.post("/connection/disconnect", status_code=status.HTTP_201_CREATED)
def report_connection_disconnect(event: ConnectionEvent) -> None:
    """Report that an android device disconnected from a beacon."""
    record_connection_event(event, action="DISCONNECTED")


@router.post("/shift/start", status_code=status.HTTP_201_CREATED)
def report_shift_start(event: ShiftEvent) -> None:
    """Report that a steward started their shift."""
    record_shift_event(event, action="SHIFT_STARTED")


@router.post("/shift/stop", status_code=status.HTTP_201_CREATED)
def report_shift_stop(event: ShiftEvent) -> None:
    """Report that a steward stopped their shift."""
    record_shift_event(event, action="SHIFT_STOPPED")
