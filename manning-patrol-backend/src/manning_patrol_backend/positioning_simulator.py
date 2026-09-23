"""
Positioning Simulator

A simulator implementation of the Positioning Interface contract.
Serves fixture data directly - assumes fixtures are already aligned with contract.
"""
import asyncio
import json
from pathlib import Path

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Positioning Simulator")

# CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# Load fixtures directly - no transformation, assume correct format
def load_fixture(filename: str):
    """Load JSON fixture file from fixtures directory."""
    fixtures_dir = Path(__file__).parent.parent.parent / "fixtures"
    fixture_path = fixtures_dir / filename
    if not fixture_path.exists():
        return []
    with open(fixture_path) as f:
        return json.load(f)


# Load fixture data
shift_data = load_fixture("fixture-shifts.json")
observation_data = load_fixture("fixture-observations.json") ## use this for now

#func takes obs_data, sorts it and if user inputs 'as_of' then remove events up untill as_of timestamp
#returns the list of events that are OBSERVED to showcase that a steward is there(assuming no beacon connec error)

def get_timestamp(e):
    return e["timestamp"]

def observed_events(events: list[dict], as_of: str | None = None) -> list[dict]:
    sorted_events = sorted(events, key=get_timestamp)

    if as_of is not None:
        sorted_events = [e for e in sorted_events if e["timestamp"] <= as_of]

    open_connections: dict[str, dict] = {}
    for event in sorted_events:
        key = event["beacon_id"]
        if event["event_type"] == "OBSERVED":
            open_connections[key] = event
        elif event["event_type"] == "NOT_OBSERVED":
            open_connections.pop(key, None)

    return list(open_connections.values())


@app.get("/observations")
async def get_observations(as_of: str | None = None):
    return observed_events(observation_data,as_of)


@app.get("/observation-events")
async def get_observation_events():
    """Returns fixture shift data as events."""
    return shift_data


@app.websocket("/ws/observation-events")
async def websocket_events(websocket: WebSocket):
    """WebSocket stream of fixture shift data."""
    await websocket.accept()
    for event in shift_data:
        await websocket.send_json(event)
        await asyncio.sleep(0.1)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "message": "Positioning Simulator running"}
