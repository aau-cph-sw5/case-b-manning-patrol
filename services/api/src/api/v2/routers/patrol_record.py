from uuid import UUID

from fastapi import APIRouter

from src.api.v2.dependencies import AsyncDbSessionDep
from src.db.models.event import Event
from src.db.repository.event import (
    get_latest_start_event,
    get_connection_events_by_android_id,
)

router = APIRouter(tags=["patrol_record"])


@router.get("/record")
async def get_records(android_id: UUID, session: AsyncDbSessionDep):
    """
    To be implemented by calling the functions
    defined below. Pass session and android_id to downstream functions
    """
    pass


async def build_records(android_id: UUID, session: AsyncDbSessionDep):
    """
    Entrypoint for building all records related to one android_id
    """
    pass
