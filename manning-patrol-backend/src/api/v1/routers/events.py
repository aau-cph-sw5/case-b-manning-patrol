
from fastapi import APIRouter, Depends
from sqlmodel import Session
from src.models import ConnectionEvent, EventStore, EventType, Datasheet
from src.services.db import get_session

router = APIRouter()

@router.post("/api/v1/connection/connect")
def connection_connect(
        payload: ConnectionEvent,
        session: Session = Depends(get_session)
):
        event = EventStore(
            event_type=EventType.CONNECT,
            timestamp=payload.timestamp,
            beacon_id=payload.beacon_id,
            android_id=payload.android_id
        )
        session.add(event)
        session.commit()

        beacon_location = session.get(Datasheet, payload.beacon_id)
        return {"ok": True}

@router.post("/api/v1/connection/disconnect")
def connection_disconnect(
        payload: ConnectionEvent,
        session: Session = Depends(get_session)
):
        event = EventStore(
            event_type=EventType.DISCONNECT,
            timestamp=payload.timestamp,
            beacon_id=payload.beacon_id,
            android_id=payload.android_id
        )
        session.add(event)
        session.commit()
        return {"ok": True}
