from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel

from src.models.event import EventType


class EventModel(BaseModel):
    event_id: UUID
    event_type: EventType
    actor: str
    beacon: str | None
    device_timestamp: datetime
    server_timestamp: datetime


class CorrectedFact(BaseModel):
    fact_type: EventType
    beacon_id: str | None = None
    occurred_at: datetime


class AdjustmentModel(BaseModel):
    adjustment_id: UUID
    target_event_id: UUID | None = None
    actor: str
    corrected_fact: CorrectedFact
    reason: str
    author: str
    server_timestamp: datetime


class MainProducer:
    @staticmethod
    async def append_event(
        event_type: EventType,
        actor: str,
        device_timestamp: datetime,
        beacon: str | None = None,
    ) -> EventModel:

        await validate_event(actor, beacon)

        event_model = EventModel(
            event_id=uuid4(),
            event_type=event_type,
            actor=actor,
            beacon=beacon,
            device_timestamp=device_timestamp,
            server_timestamp=_now_utc(),
        )

        await _send_event_model_tester(event_model)
        return event_model

    @staticmethod
    async def append_adjustment(
        actor: str,
        corrected_fact: CorrectedFact,
        reason: str,
        author: str,
        target_event_id: UUID | None = None,
    ) -> AdjustmentModel:

        adjustment_model = AdjustmentModel(
            adjustment_id=uuid4(),
            target_event_id=target_event_id,
            actor=actor,
            corrected_fact=corrected_fact,
            reason=reason,
            author=author,
            server_timestamp=_now_utc(),
        )

        await _send_adjustment_model_tester(adjustment_model)
        return adjustment_model


async def _send_event_model_tester(event_model: EventModel) -> EventModel:
    print(event_model)
    return event_model


async def _send_adjustment_model_tester(
    adjustment_model: AdjustmentModel,
) -> AdjustmentModel:
    print(adjustment_model)
    return adjustment_model


def _now_utc() -> datetime:
    return datetime.now(UTC)


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
