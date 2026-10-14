from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi.exceptions import RequestValidationError
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.repository.events import get_event, insert_adjustment, insert_event
from src.models.event import AdjustmentModel, CorrectedFact, EventModel, EventType


class MainProducer:
    @staticmethod
    async def append_event(
        session: AsyncSession,
        event_type: EventType,
        android_id: UUID,
        device_timestamp: datetime,
        source: str,
        beacon_id: UUID | None = None,
    ) -> EventModel:

        await validate_event(android_id, beacon_id)

        event_model = EventModel(
            event_id=uuid4(),
            event_type=event_type,
            android_id=android_id,
            beacon_id=beacon_id,
            device_timestamp=device_timestamp,
            server_timestamp=_now_utc(),
            source=source,
        )

        await insert_event(session, event_model)
        return event_model

    @staticmethod
    async def append_adjustment(
        session: AsyncSession,
        android_id: UUID,
        corrected_fact: CorrectedFact,
        reason: str,
        author: str,
        source: str,
        target_event_id: UUID | None = None,
    ) -> AdjustmentModel:

        if ((corrected_fact.fact_type == EventType.CONNECT_EVENT or
             corrected_fact.fact_type == EventType.DISCONNECT_EVENT) and
             corrected_fact.beacon_id is None):
            raise RequestValidationError("Connect and Disconnect event needs beacon")

        if (target_event_id is not None):
            try:
                await get_event(session, target_event_id)
            except Exception:
                raise EventValidationError("target event id does not exist") from None


        adjustment_model = AdjustmentModel(
            adjustment_id=uuid4(),
            target_event_id=target_event_id,
            android_id=android_id,
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


class AndroidIddNotFoundError(EventValidationError):
    pass


class BeaconNotFoundError(EventValidationError):
    pass


async def validate_event(
    android_id: UUID,
    beacon_id: UUID | None = None,
) -> None:
    android_id_found = await return_actor(android_id)

    if android_id_found is None:
        raise AndroidIddNotFoundError(f"Android_id '{android_id}' was not found")

    if beacon_id is not None:
        beacon_found = await return_beacon(beacon_id)

        if beacon_found is None:
            raise BeaconNotFoundError(f"Beacon '{beacon_id}' was not found")


# CHANGE TO GET VALID ACTOR/ANDROID ID FROM DB. RETURN ACTOR OR NONE
async def return_actor(android_id: UUID) -> str | None:
    return "Actor1"


# CHANGE TO GET VALID BEACON ID FROM DB. RETURN BEACON OR NONE
async def return_beacon(beacon_id: UUID) -> str | None:
    return "Beacon1"
