"""
Positioning Simulator

A simulator implementation of the Positioning Interface contract.
Serves fixture data directly - assumes fixtures are already aligned with contract.
"""

from fastapi import APIRouter, WebSocket

from src.services.positioning_service import load_fixture, simulate_event_stream

router = APIRouter(tags=["positioning-simulator"])

# Load fixture events for WebSocket streaming
events = load_fixture("fixture-events-v1.json")


@router.websocket("/ws/observation-events")
async def websocket_events(websocket: WebSocket):
    """WebSocket stream of fixture patrol session data."""
    await websocket.accept()

    await simulate_event_stream(events, websocket)
