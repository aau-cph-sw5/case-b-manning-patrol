"""
Ingestion event log.

Connection and patrol session events arrive one action per endpoint (contracts/
positioning-ingestion/v1) and are appended here. The stored connection events
keep the shape of fixtures/fixture-events-v1.json, so what the app posts is
indistinguishable from what the simulator streams. In-memory for now; the
persistence layer is a later backlog item.
"""

from src.models.connection_event import ConnectionEvent
from src.models.patrol_session_event import PatrolSessionEvent
from src.models.patrol_session_event_v2 import PatrolSessionEventV2

connection_log: list[dict[str, str]] = []
patrol_session_log: list[dict[str, str]] = []


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
    # one line per received event: the terminal shows what actually arrived,
    # where the client's console.log only shows what left the phone
    print(
        f"received {action}: {event.android_id} at beacon {event.beacon_id}"
        f" ({event.timestamp.isoformat()})"
    )


def record_patrol_session_event(event: PatrolSessionEvent, action: str) -> None:
    """Append a patrol session start or stop to the log."""
    patrol_session_log.append({
        "event": action, 
         "android_id": event.id,
        "timestamp": event.timestamp.isoformat()})
    print(f"received {action}: {event.id}")


def record_patrol_session_event_v2(
    event: PatrolSessionEventV2, action: str
) -> None:
    """Append a timestamped v2 patrol-session action."""
    patrol_session_log.append(
        {
            "event": action,
            "android_id": event.android_id,
            "timestamp": event.timestamp.isoformat(),
        }
    )
    print(f"received {action}: {event.android_id} ({event.timestamp.isoformat()})")
