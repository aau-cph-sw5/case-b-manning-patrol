"""
Health

Health check endpoint for the backend.
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.main import get_session

router = APIRouter(tags=["health"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "message": "Manning Patrol Backend running"}


@router.get("/health/db")
async def db_health(session: SessionDep) -> dict:
    """Check that the database connection works."""
    result = await session.exec(select(1))
    result.one()
    return {"database": "up"}
