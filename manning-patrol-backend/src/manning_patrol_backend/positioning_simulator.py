"""
Positioning Simulator

A simulator implementation of the Positioning Interface contract.
Serves fixture data directly - assumes fixtures are already aligned with contract.
"""
import asyncio

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from .services.positioning_service import observed_events, load_fixture

app = FastAPI(title="Positioning Simulator")

# CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load fixture data
shift_data = load_fixture("fixture-shifts-v1.json")
observation_data = load_fixture("fixture-observations-v1.json") ## use this for now

#func takes obs_data, sorts it and if user inputs 'as_of' then remove events up untill as_of timestamp
#returns the list of events that are OBSERVED to showcase that a steward is there(assuming no beacon connec error)

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
