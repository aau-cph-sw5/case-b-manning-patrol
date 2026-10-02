import uuid
from enum import Enum


class EventType(str, Enum):
    CONNECT_EVENT = 'connection'
    DISCONNECT_EVENT = 'disconnection'
    START_EVENT = 'start'
    STOP_EVENT = 'stop'
    

class ConnectionEvent:
    android_id: str
    beacon_id: str
    timestamp: str


class EventModel:
    event_type: str




