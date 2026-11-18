"""Validate and store incoming steward events and supervisor adjustments."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.exc import NoResultFound
from sqlmodel.ext.asyncio.session import AsyncSession

from src.api.v2.schemas.adjustment import AdjustmentEventStored, CorrectedFact
from src.db.models.adjustment import Adjustment
from src.db.models.adjustment_author import AdjustmentAuthor
from src.db.models.event import Event
from src.db.models.integrity_chain_link import IntegrityChainLink
from src.db.repository.adjustment import insert_adjustment
from src.db.repository.event import get_event, get_open_connections, insert_event
from src.db.repository.steward_shift_identity import get_or_create_steward_ref
from src.domain.event import EventType
from src.services.hash_chain.chain_linker import ChainLinker
from src.services.hash_chain.entry_stringifier import ChainEntry
from src.services.shared.shift_schedule import ShiftSchedule

from .exceptions import (
    AndroidIdNotFoundError,
    BeaconNotFoundError,
    EventValidationError,
    TargetEventNotFoundError,
)


class EventProducer:
    """Append events and adjustments, stamping server time and source."""

    def __init__(self, session: AsyncSession, source: str) -> None:
        self._session = session
        self._source = source
        self._shift_schedule = ShiftSchedule.from_file()

    async def _get_chain_link(self, chain_entry: ChainEntry) -> IntegrityChainLink:
        linker = ChainLinker(self._session, chain_entry)
        return await linker.link(source=self._source)

    async def append_event(
        self,
        event_type: EventType,
        android_id: UUID,
        device_timestamp: datetime,
        beacon_id: UUID | None = None,
    ) -> Event:
        """Validate and store a new event and return it.

        The event is stored under the steward's reference for the scheduled
        shift running at ``device_timestamp``, never under ``android_id``;
        the reference is created on the steward's first event of the shift.
        The server timestamp is set to the current time. Raises
        AndroidIdNotFoundError or BeaconNotFoundError for an unknown device or
        beacon, but both lookups are placeholders that accept every ID.
        """
        await self._validate_event(android_id, beacon_id)
        shift = self._shift_schedule.latest_shift(device_timestamp)
        steward_ref = await get_or_create_steward_ref(
            self._session, android_id, shift.start
        )
        return await self._store_event(
            event_type, steward_ref, device_timestamp, beacon_id
        )

    async def close_open_connections(
        self,
        android_id: UUID,
        device_timestamp: datetime,
    ) -> list[Event]:
        """Disconnect the steward from every beacon still connected.

        Stores one DISCONNECT event at ``device_timestamp`` per open connection
        and returns the stored events. Each disconnect gets the steward
        reference of the connect it closes.
        """
        open_connections = await get_open_connections(self._session, android_id)
        pending_closures = [
            (connection.steward_ref, connection.beacon_id)
            for connection in open_connections
        ]
        closed_connections: list[Event] = []
        for steward_ref, beacon_id in pending_closures:
            closed_connections.append(
                await self._store_event(
                    EventType.DISCONNECT_EVENT,
                    steward_ref,
                    device_timestamp,
                    beacon_id,
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
            except NoResultFound:
                raise TargetEventNotFoundError(
                    "target event id does not exist"
                ) from None
        adjustment = Adjustment(
            adjustment_id=uuid4(),
            target_event_id=target_event_id,
            server_timestamp=EventProducer._now_utc(),
            source=self._source,
            corrected_fact_type=corrected_fact.fact_type,
            corrected_beacon_id=corrected_fact.beacon_id,
            corrected_occured_at=corrected_fact.occurred_at,
        )

        await insert_adjustment(
            self._session, adjustment, chain_link=await self._get_chain_link(adjustment)
        )

        adjustment_author = AdjustmentAuthor(
            adjustment_id=adjustment.adjustment_id,
            android_id=android_id,
            reason=reason,
            author=author,
            server_timestamp=EventProducer._now_utc(),
            source=self._source,
        )
        self._session.add(adjustment_author)
        await self._session.commit()
        await self._session.refresh(adjustment_author)

        return await AdjustmentEventStored.from_adjustment(adjustment, self._session)

    async def _store_event(
        self,
        event_type: EventType,
        steward_ref: UUID,
        device_timestamp: datetime,
        beacon_id: UUID | None,
    ) -> Event:
        event = Event(
            event_id=uuid4(),
            event_type=event_type,
            steward_ref=steward_ref,
            beacon_id=beacon_id,
            device_timestamp=device_timestamp,
            server_timestamp=EventProducer._now_utc(),
            source=self._source,
        )
        return await insert_event(
            self._session, event, chain_link=await self._get_chain_link(event)
        )

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

    @staticmethod
    def _now_utc() -> datetime:
        return datetime.now(UTC)
