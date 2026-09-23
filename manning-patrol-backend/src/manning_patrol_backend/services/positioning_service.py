import json
from pathlib import Path

def get_timestamp(e):
    return e["timestamp"]

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