"""
Repository of functions used to query the database related to Events
"""

from datetime import datetime
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models.event import Adjustment, Event
from src.domain.event import EventType


async def get_event(session: AsyncSession, event_id: UUID) -> Event:
    result = await session.exec(select(Event).where(Event.event_id == event_id))

    return result.one()


async def get_events(session: AsyncSession) -> list[Event]:
    result = await session.exec(select(Event))

    return list(result.all())


async def get_open_connections(session: AsyncSession, android_id: UUID) -> list[Event]:
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


async def get_adjustment(session: AsyncSession, adjustment_id: UUID) -> Adjustment:
    result = await session.exec(
        select(Adjustment).where(Adjustment.adjustment_id == adjustment_id)
    )
    return result.one()


async def get_adjustments(session: AsyncSession) -> list[Adjustment]:
    result = await session.exec(select(Adjustment))

    return list(result.all())


async def insert_adjustment(
    session: AsyncSession,
    adjustment: Adjustment,
) -> Adjustment:
    session.add(adjustment)
    await session.commit()
    await session.refresh(adjustment)
    return adjustment
