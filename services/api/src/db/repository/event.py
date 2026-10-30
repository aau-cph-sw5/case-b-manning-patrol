"""Queries for steward events."""

from datetime import datetime
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models.event import Event
from src.domain.event import EventType


async def get_event(session: AsyncSession, event_id: UUID) -> Event:
    result = await session.exec(select(Event).where(Event.event_id == event_id))

    return result.one()


async def get_events(session: AsyncSession) -> list[Event]:
    result = await session.exec(select(Event))

    return list(result.all())


async def get_open_connections(session: AsyncSession, android_id: UUID) -> list[Event]:
    """Return the steward's CONNECT events that have not been disconnected.

    For each beacon, returns the latest CONNECT if it is later than the latest
    DISCONNECT for that beacon, by device timestamp.
    """
    connects = await session.exec(
        select(Event).where(
            Event.android_id == android_id,
            Event.event_type == EventType.CONNECT_EVENT,
        )
    )
    disconnects = await session.exec(
        select(Event).where(
            Event.android_id == android_id,
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


async def insert_event(session: AsyncSession, event: Event) -> Event:
    session.add(event)
    await session.commit()
    await session.refresh(event)
    return event
