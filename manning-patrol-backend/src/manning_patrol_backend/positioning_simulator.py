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


@app.get("/observations")
async def get_observations():
    """Returns fixture shift data."""
    return shift_data


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
