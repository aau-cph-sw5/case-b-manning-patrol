"""Validate and store incoming steward events and supervisor adjustments."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlmodel.ext.asyncio.session import AsyncSession

from src.api.v2.schemas.adjustment import AdjustmentEventStored, CorrectedFact
from src.db.models.adjustment import Adjustment
from src.db.models.event import Event
from src.db.repository.adjustment import insert_adjustment
from src.db.repository.event import get_event, get_open_connections, insert_event
from src.domain.event import EventType


class EventProducer:
    """Append events and adjustments, stamping server time and source."""

    def __init__(self, session: AsyncSession, source: str) -> None:
        self._session = session
        self._source = source

    async def append_event(
        self,
        event_type: EventType,
        android_id: UUID,
        device_timestamp: datetime,
        beacon_id: UUID | None = None,
    ) -> Event:
        """Validate and store a new event and return it.

        The server timestamp is set to the current time. Raises
        AndroidIdNotFoundError or BeaconNotFoundError for an unknown device or
        beacon, but both lookups are placeholders that accept every ID.
        """
        await self._validate_event(android_id, beacon_id)

        event = Event(
            event_id=uuid4(),
            event_type=event_type,
            android_id=android_id,
            beacon_id=beacon_id,
            device_timestamp=device_timestamp,
            server_timestamp=_now_utc(),
            source=self._source,
        )

        await insert_event(self._session, event)
        return event

    async def close_open_connections(
        self,
        android_id: UUID,
        device_timestamp: datetime,
    ) -> list[Event]:
        """Disconnect the steward from every beacon still connected.

        Stores one DISCONNECT event at ``device_timestamp`` per open connection
        and returns the stored events.
        """
        open_connections = await get_open_connections(self._session, android_id)
        pending_closures = [
            (connection.android_id, connection.beacon_id)
            for connection in open_connections
        ]
        closed_connections: list[Event] = []
        for connection_android_id, connection_beacon_id in pending_closures:
            closed_connections.append(
                await self.append_event(
                    event_type=EventType.DISCONNECT_EVENT,
                    android_id=connection_android_id,
                    beacon_id=connection_beacon_id,
                    device_timestamp=device_timestamp,
                )
            )
        return closed_connections

    async def append_adjustment(
        self,
        android_id: UUID,
        corrected_fact: CorrectedFact,
        reason: str,
        author: str,
        target_event_id: UUID | None = None,
    ) -> AdjustmentEventStored:
        """Validate and store a supervisor's correction.

        Raises EventValidationError if a connect or disconnect correction has no
        beacon, and TargetEventNotFoundError if ``target_event_id`` is given but
        the event cannot be loaded.
        """
        if (
            corrected_fact.fact_type == EventType.CONNECT_EVENT
            or corrected_fact.fact_type == EventType.DISCONNECT_EVENT
        ) and corrected_fact.beacon_id is None:
            raise EventValidationError("Connect and Disconnect event needs beacon")

        if target_event_id is not None:
            try:
                await get_event(self._session, target_event_id)
            except Exception:
                raise TargetEventNotFoundError(
                    "target event id does not exist"
                ) from None

        adjustment = Adjustment(
            adjustment_id=uuid4(),
            target_event_id=target_event_id,
            android_id=android_id,
            reason=reason,
            author=author,
            server_timestamp=_now_utc(),
            source=self._source,
            corrected_fact_type=corrected_fact.fact_type,
            corrected_beacon_id=corrected_fact.beacon_id,
            corrected_occured_at=corrected_fact.occurred_at,
        )

        await insert_adjustment(self._session, adjustment)
        return AdjustmentEventStored.from_adjustment(adjustment)

    async def _validate_event(self, android_id: UUID, beacon_id: UUID | None) -> None:
        if await self._find_android_id(android_id) is None:
            raise AndroidIdNotFoundError(f"Android_id '{android_id}' was not found")

        if beacon_id is not None and await self._find_beacon(beacon_id) is None:
            raise BeaconNotFoundError(f"Beacon '{beacon_id}' was not found")

    async def _find_android_id(self, android_id: UUID) -> str | None:
        """Look up a device.

        Placeholder that accepts every ID until a device registry exists.
        """
        return "Android_1"

    async def _find_beacon(self, beacon_id: UUID) -> str | None:
        """Look up a beacon.

        Placeholder that accepts every ID until beacons are checked against
        patrol areas.
        """
        return "Beacon_1"


def _now_utc() -> datetime:
    return datetime.now(UTC)


class EventValidationError(Exception):
    """An event or adjustment is invalid; the API answers 400."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class TargetEventNotFoundError(Exception):
    """An adjustment targets an event that does not exist; the API answers 404."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class AndroidIdNotFoundError(Exception):
    """The device that sent an event is not known."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class BeaconNotFoundError(Exception):
    """An event refers to a beacon that is not known."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
