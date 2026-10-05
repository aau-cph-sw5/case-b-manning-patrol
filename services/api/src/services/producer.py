import uuid
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel


class EventType(StrEnum):
    CONNECT_EVENT = "connection"
    DISCONNECT_EVENT = "disconnection"
    START_EVENT = "start"
    STOP_EVENT = "stop"
    ADJUSTMENT_EVENT = "adjustment"


class EventModel(BaseModel):
    event_id: str
    event_type: EventType
    actor: str
    beacon: str | None
    device_timestamp: str
    server_timestamp: str
    # source: api/simulator/import


class MainProducer:
    @staticmethod
    async def append_event(
        event_type: EventType,
        actor: str,
        device_timestamp: str,
        beacon: str | None = None,
    ) -> EventModel:

        await validate_event(actor, beacon)

        event_model = EventModel(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            actor=actor,
            beacon=beacon,
            device_timestamp=device_timestamp,
            server_timestamp=_now_utc_iso(),
        )

        await _send_model_tester(event_model)
        return event_model


async def _send_model_tester(event_model: EventModel) -> EventModel:
    print(event_model)
    return event_model


def _now_utc_iso() -> str:
    return datetime.now(UTC).isoformat()


class EventValidationError(Exception):
    pass


class ActorNotFoundError(EventValidationError):
    pass


class BeaconNotFoundError(EventValidationError):
    pass


async def validate_event(
    actor: str,
    beacon: str | None = None,
) -> None:
    actor_found = await return_actor(actor)

    if actor_found is None:
        raise ActorNotFoundError(f"Actor '{actor}' was not found")

    if beacon is not None:
        beacon_found = await return_beacon(beacon)

        if beacon_found is None:
            raise BeaconNotFoundError(f"Beacon '{beacon}' was not found")


# CHANGE TO GET VALID ACTOR/ANDROID ID FROM DB. RETURN ACTOR OR NONE
async def return_actor(actor: str) -> str | None:
    return "Actor1"


# CHANGE TO GET VALID BEACON ID FROM DB. RETURN BEACON OR NONE
async def return_beacon(beacon: str) -> str | None:
    return "Beacon1"
