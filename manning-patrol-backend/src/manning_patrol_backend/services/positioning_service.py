import json
import asyncio
from pathlib import Path
from datetime import datetime

SPEED = 100  # 100x faster than real time


def get_timestamp(e):
    return e["timestamp"]


def get_event_delay(previous_event, current_event):
    """Calculate the delay between two events based on their timestamps"""
    previous_timestamp = previous_event["timestamp"]
    current_timestamp = current_event["timestamp"]

    previous_time = datetime.fromisoformat(previous_timestamp)
    current_time = datetime.fromisoformat(current_timestamp)

    delay = ((current_time - previous_time) / SPEED).total_seconds() #SPEED is used to speed up the simulation, so we divide the actual delay by SPEED
    return delay

async def simulate_event_stream(events, websocket):
    """Simulate a stream of events over a WebSocket connection"""
    for i in range(len(events)-1):
        await websocket.send_json(events[i])
        delay = get_event_delay(events[i], events[i + 1])
        await asyncio.sleep(delay)
    # Send the last event
    await websocket.send_json(events[len(events)-1])

def check_short_disconnects(previous_event, current_event):
    """Check if the signal is just lost between two events based on their timestamps"""
    previous_time = datetime.fromisoformat(previous_event["timestamp"])
    current_time = datetime.fromisoformat(current_event["timestamp"])

    time_difference = (current_time - previous_time).total_seconds()
    
    if time_difference < 8:  # Assuming a signal is considered lost if an event is disconnected and then connected again in less than 8 seconds
        previous_beacon_id = previous_event["beacon_id"]
        current_beacon_id = current_event["beacon_id"]
        if previous_beacon_id == current_beacon_id:
            if previous_event["event_type"] == "NOT_OBSERVED" and current_event["event_type"] == "OBSERVED":
                # prints the short disconnects to the console for debugging purposes
                """print(
                        f"short disconnect: {previous_event['beacon_id']} "
                        f"{previous_time} -> {current_time}"
                )"""
                return True
    return False


def filter_short_disconnects(events):
    """Filter out short disconnects from the event stream"""
    filtered_events = []
    i = 0
    while i < len(events) - 1:
        if check_short_disconnects(events[i], events[i + 1]):
            i += 2  # Skip the next 2 events if it's a short disconnect
        else:
            filtered_events.append(events[i]) # keep the event
            i += 1 # move to the next event
    # Add the last event if it's not part of a short disconnect
    if i == len(events) - 1:
        filtered_events.append(events[i])
    return filtered_events


def observed_events(events: list[dict], as_of: str | None = None) -> list[dict]:
    sorted_events = sorted(events, key=get_timestamp)

    if as_of is not None:
        sorted_events = [e for e in sorted_events if e["timestamp"] <= as_of]

    observed_connections: dict[str, dict] = {}
    for event in sorted_events:
        key = event["beacon_id"]
        if event["event_type"] == "OBSERVED":
            observed_connections[key] = event
        elif event["event_type"] == "NOT_OBSERVED":
            observed_connections.pop(key, None)

    return list(observed_connections.values())

# Load fixtures directly - no transformation, assume correct format
def load_fixture(filename: str):
    """Load JSON fixture file from fixtures directory."""
    fixtures_dir = Path(__file__).parent.parent.parent.parent / "fixtures"
    fixture_path = fixtures_dir / filename
    if not fixture_path.exists():
        return []
    with open(fixture_path) as f:
        return json.load(f)