"""
Positioning Simulator

A simulator implementation of the Positioning Interface contract.
Serves fixture data directly - assumes fixtures are already aligned with contract.
"""
import asyncio

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from .services.positioning_service import simulate_event_stream, load_fixture

app = FastAPI(title="Positioning Simulator")

# CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load fixture data
events = load_fixture("fixture-events-v1.json")  # Load fixture events for WebSocket streaming



@app.websocket("/ws/observation-events")
async def websocket_events(websocket: WebSocket):
    """WebSocket stream of fixture shift data."""
    await websocket.accept()

    await simulate_event_stream(events, websocket)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "message": "Positioning Simulator running"}
