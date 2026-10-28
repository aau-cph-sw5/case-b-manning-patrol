from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi.exceptions import RequestValidationError
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.repository.events import (
    get_event,
    get_open_connections,
    insert_adjustment,
    insert_event,
)
from src.models.event import (
    Adjustment,
    AdjustmentStored,
    CorrectedFact,
    Event,
    EventType,
)


class MainProducer:
    @staticmethod
    async def append_event(
        session: AsyncSession,
        event_type: EventType,
        android_id: UUID,
        device_timestamp: datetime,
        source: str,
        beacon_id: UUID | None = None,
    ) -> Event:

        await validate_event(android_id, beacon_id)

        event = Event(
            event_id=uuid4(),
            event_type=event_type,
            android_id=android_id,
            beacon_id=beacon_id,
            device_timestamp=device_timestamp,
            server_timestamp=_now_utc(),
            source=source,
        )

        await insert_event(session, event)
        return event

    @staticmethod
    async def close_open_connections(
        session: AsyncSession,
        android_id: UUID,
        device_timestamp: datetime,
        source: str,
    ) -> list[Event]:
        open_connections = await get_open_connections(session, android_id)
        pending_closures = [
            (connection.android_id, connection.beacon_id)
            for connection in open_connections
        ]
        closed_connections: list[Event] = []
        for connection_android_id, connection_beacon_id in pending_closures:
            closed_connections.append(
                await MainProducer.append_event(
                    session=session,
                    event_type=EventType.DISCONNECT_EVENT,
                    android_id=connection_android_id,
                    beacon_id=connection_beacon_id,
                    device_timestamp=device_timestamp,
                    source=source,
                )
            )
        return closed_connections

    @staticmethod
    async def append_adjustment(
        session: AsyncSession,
        android_id: UUID,
        corrected_fact: CorrectedFact,
        reason: str,
        author: str,
        source: str,
        target_event_id: UUID | None = None,
    ) -> AdjustmentStored:

        if (
            corrected_fact.fact_type == EventType.CONNECT_EVENT
            or corrected_fact.fact_type == EventType.DISCONNECT_EVENT
        ) and corrected_fact.beacon_id is None:
            raise RequestValidationError("Connect and Disconnect event needs beacon")

        if target_event_id is not None:
            try:
                await get_event(session, target_event_id)
            except Exception:
                raise EventValidationError("target event id does not exist") from None

        adjustment = Adjustment(
            adjustment_id=uuid4(),
            target_event_id=target_event_id,
            android_id=android_id,
            reason=reason,
            author=author,
            server_timestamp=_now_utc(),
            source=source,
            corrected_fact_type=corrected_fact.fact_type,
            corrected_beacon_id=corrected_fact.beacon_id,
            corrected_occured_at=corrected_fact.occurred_at,
        )

        await insert_adjustment(session, adjustment)
        return AdjustmentStored.from_adjustment(adjustment)


def _now_utc() -> datetime:
    return datetime.now(UTC)


class EventValidationError(Exception):
    pass


class AndroidIddNotFoundError(EventValidationError):
    pass


class BeaconNotFoundError(EventValidationError):
    pass


async def validate_event(
    android_id: UUID,
    beacon_id: UUID | None = None,
) -> None:
    android_id_found = await return_android_id(android_id)

    if android_id_found is None:
        raise AndroidIddNotFoundError(f"Android_id '{android_id}' was not found")

    if beacon_id is not None:
        beacon_found = await return_beacon(beacon_id)

        if beacon_found is None:
            raise BeaconNotFoundError(f"Beacon '{beacon_id}' was not found")


async def return_android_id(android_id: UUID) -> str | None:
    return "Android_1"


async def return_beacon(beacon_id: UUID) -> str | None:
    return "Beacon_1"
