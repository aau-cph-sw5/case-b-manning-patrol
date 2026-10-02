import uuid
from enum import Enum
from datetime import datetime, timezone


class EventType(str, Enum):
    CONNECT_EVENT = 'connection'
    DISCONNECT_EVENT = 'disconnection'
    START_EVENT = 'start'
    STOP_EVENT = 'stop'
    ADJUSTMENT_EVENT = 'adjustment'
    

class EventModel:
    event_id: str 
    event_type: EventType
    actor: str
    device_timestamp: str
    server_timestamp: str
    #source: api/simulator/import


class MainProducer: 

    def __init__(self, EventStore):
        self._store = EventStore 
         #ADD EVENTSTORE FUNCTIONALITY


    async def Append(self, event_type, actor, device_timestamp) -> EventModel:
        eventmodel = EventModel(
            event_id = str(uuid.uuid4()),
            event_type = event_type,
            actor = actor,
            device_timestamp = device_timestamp,
            server_timestamp = _now_utc_iso,
        )
        await SendModelTester(eventmodel)
        return eventmodel


        

def SendModelTester(eventmodel):
    print(eventmodel)
    return eventmodel


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


