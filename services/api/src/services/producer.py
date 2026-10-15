from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.repository.events import (
    get_open_connections,
    insert_adjustment,
    insert_event,
)
from src.models.event import AdjustmentModel, CorrectedFact, EventModel, EventType


class MainProducer:
    @staticmethod
    async def append_event(
        session: AsyncSession,
        event_type: EventType,
        actor: str,
        device_timestamp: datetime,
        source: str,
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
            source=source,
        )

        await insert_event(session, event_model)
        return event_model

    @staticmethod
    @staticmethod
    async def close_open_connections(
        session: AsyncSession,
        actor: str,
        device_timestamp: datetime,
        source: str,
    ) -> list[EventModel]:
        open_connections = await get_open_connections(session, actor)
        pending_closures = [
            (connection.actor, connection.beacon) for connection in open_connections
        ]
        closed_connections = []
        for connection_actor, connection_beacon in pending_closures:
            closed_connections.append(
                await MainProducer.append_event(
                    session=session,
                    event_type=EventType.DISCONNECT_EVENT,
                    actor=connection_actor,
                    beacon=connection_beacon,
                    device_timestamp=device_timestamp,
                    source=source,
                )
            )
        return closed_connections

    @staticmethod
    async def append_adjustment(
        session: AsyncSession,
        actor: str,
        corrected_fact: CorrectedFact,
        reason: str,
        author: str,
        source: str,
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
            source=source,
        )

        await insert_adjustment(session, adjustment_model)
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
