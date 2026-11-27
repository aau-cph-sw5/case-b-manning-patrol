"""Endpoint for a steward's patrol records in the current shift."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.exc import SQLAlchemyError

from src.api.v2.dependencies import AsyncDbSessionDep
from src.api.v2.schemas.patrol_record import RecordList
from src.authorization.dependencies import require_permission
from src.security.current_user import User
from src.services.patrol_record.record_builder import RecordBuildError, build_records

router = APIRouter(tags=["patrol_record"])


@router.get("/record")
async def get_records(
    android_id: UUID,
    session: AsyncDbSessionDep,
    user: Annotated[
        User, Depends(require_permission("steward_own_patrol_record_view"))
    ],
) -> RecordList:
    """Return the steward's patrol records for the current shift, most recent first.

    Raises RecordBuildError if the database cannot be read.
    """

    try:
        return await build_records(session, android_id)
    except SQLAlchemyError as error:
        raise RecordBuildError("Could not read the steward's patrol records") from error
