"""Queries for steward events."""

from datetime import datetime
from uuid import UUID

from sqlmodel import col, func, select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import SelectOfScalar

from src.db.models.event import Event
from src.db.models.integrity_chain_link import ChainName, IntegrityChainLink
from src.db.models.steward_shift_identity import StewardShiftIdentity
from src.domain.event import EventType


def _events_of_steward(android_id: UUID) -> SelectOfScalar[Event]:
    """Select the events of every shift the steward has worked.

    Events only store ``steward_ref``, so the device is matched through the
    steward identity table.
    """
    return (
        select(Event)
        .join(
            StewardShiftIdentity,
            col(Event.steward_ref) == col(StewardShiftIdentity.steward_ref),
        )
        .where(StewardShiftIdentity.android_id == android_id)
    )


async def get_event(session: AsyncSession, event_id: UUID) -> Event:
    """Return the event with this ID, or raise NoResultFound."""
    result = await session.exec(select(Event).where(Event.event_id == event_id))

    return result.one()


async def get_events(
    session: AsyncSession,
    *,
    known_at: datetime | None = None,
) -> list[Event]:
    """Return the stored events, in no particular order.

    With ``known_at``, only events the backend had received by then
    (``server_timestamp <= known_at``) are returned, so a past picture can be
    rebuilt without events that arrived later. ``None`` returns every event.
    """
    statement = select(Event)
    if known_at is not None:
        statement = statement.where(col(Event.server_timestamp) <= known_at)
    result = await session.exec(statement)

    return list(result.all())


async def get_latest_start_event(
    session: AsyncSession, android_id: UUID
) -> Event | None:
    """Return the steward's most recent shift start event, or None if never started."""
    result = await session.exec(
        _events_of_steward(android_id)
        .where(Event.event_type == EventType.START_EVENT)
        .order_by(col(Event.device_timestamp).desc())
    )

    return result.first()


async def get_connection_events_by_android_id(
    session: AsyncSession, android_id: UUID, since: datetime
) -> list[Event]:
    """Return the steward's connect/disconnect events from `since` on, oldest first."""
    result = await session.exec(
        _events_of_steward(android_id)
        .where(
            col(Event.event_type).in_(
                [EventType.CONNECT_EVENT, EventType.DISCONNECT_EVENT],
            ),
            col(Event.device_timestamp) >= since,
        )
        .order_by(col(Event.device_timestamp))
    )

    return list(result.all())


async def get_open_connections(session: AsyncSession, android_id: UUID) -> list[Event]:
    """Return the steward's CONNECT events that have not been disconnected.

    For each beacon, returns the latest CONNECT if it is later than the latest
    DISCONNECT for that beacon, by device timestamp.
    """
    connects = await session.exec(
        _events_of_steward(android_id).where(
            Event.event_type == EventType.CONNECT_EVENT,
        )
    )
    disconnects = await session.exec(
        _events_of_steward(android_id).where(
            Event.event_type == EventType.DISCONNECT_EVENT,
        )
    )

    latest_disconnect: dict[UUID | None, datetime] = {}
    for disconnect in disconnects:
        if (
            disconnect.beacon_id not in latest_disconnect
            or disconnect.device_timestamp > latest_disconnect[disconnect.beacon_id]
        ):
            latest_disconnect[disconnect.beacon_id] = disconnect.device_timestamp

    open_connections: dict[UUID | None, Event] = {}
    for connect in connects:
        is_open = (
            connect.beacon_id not in latest_disconnect
            or connect.device_timestamp > latest_disconnect[connect.beacon_id]
        )
        is_latest = connect.beacon_id not in open_connections or (
            connect.device_timestamp
            > open_connections[connect.beacon_id].device_timestamp
        )
        if is_open and is_latest:
            open_connections[connect.beacon_id] = connect

    return list(open_connections.values())


async def count_unlinked_events(session: AsyncSession) -> int:
    """Return how many events have no link in the events hash chain.

    ``insert_event`` saves every event together with its link, so this is 0
    unless rows were written to the database directly, for example by the
    seed script or by someone editing the database.
    """
    linked_ids = select(IntegrityChainLink.record_id).where(
        IntegrityChainLink.chain == ChainName.EVENTS
    )
    result = await session.exec(
        select(func.count())
        .select_from(Event)
        .where(col(Event.event_id).not_in(linked_ids))
    )

    return result.one()


async def insert_event(
    session: AsyncSession, event: Event, chain_link: IntegrityChainLink
) -> Event:
    """Insert and commit the event, then reload it from the database."""
    session.add(event)
    session.add(chain_link)
    await session.commit()
    await session.refresh(event)
    await session.refresh(chain_link)
    return event
