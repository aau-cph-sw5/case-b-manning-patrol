"""Queries for the steward identity table."""

from datetime import datetime
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models import StewardIdentity


async def get_or_create_steward_ref(
    session: AsyncSession, android_id: UUID, shift_start: datetime
) -> UUID:
    """Return the steward's reference for this shift, creating one if missing.

    The same steward gets the same reference for every call within one shift
    and a new random reference for each new shift. Creating a reference
    inserts and commits a new row.
    """
    result = await session.exec(
        select(StewardIdentity).where(
            StewardIdentity.android_id == android_id,
            StewardIdentity.shift_start == shift_start,
        )
    )
    identity = result.first()
    if identity is None:
        identity = StewardIdentity(android_id=android_id, shift_start=shift_start)
        session.add(identity)
        await session.commit()
        await session.refresh(identity)
    return identity.steward_ref
