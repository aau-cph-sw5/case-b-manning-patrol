"""
Ingestion event log.

Connection and shift events arrive one action per endpoint (contracts/
positioning-ingestion/v1) and are appended here. The stored connection events
keep the shape of fixtures/fixture-events-v1.json, so what the app posts is
indistinguishable from what the simulator streams. In-memory for now; the
persistence layer is a later backlog item.
"""

from src.models import ConnectionEvent, ShiftEvent

connection_log: list[dict[str, str]] = []
shift_log: list[dict[str, str]] = []


def record_connection_event(event: ConnectionEvent, action: str) -> None:
    """Append a beacon connect or disconnect to the log."""
    connection_log.append(
        {
            "event": action,
            "android_id": event.android_id,
            "beacon_id": event.beacon_id,
            "timestamp": event.timestamp.isoformat(),
        }
    )


def record_shift_event(event: ShiftEvent, action: str) -> None:
    """Append a shift start or stop to the log."""
    shift_log.append({"event": action, "android_id": event.id})
