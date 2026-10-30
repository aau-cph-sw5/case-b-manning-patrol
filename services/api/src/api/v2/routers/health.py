"""
Health

Health check endpoint for the backend.
"""

from fastapi import APIRouter
from sqlmodel import select

from src.api.v2.dependencies import AsyncDbSessionDep

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    """Report that the API process is up and serving requests.

    Does not touch the database; use `/health/db` to check that too.
    """
    return {"status": "ok", "message": "Manning Patrol Backend running"}


@router.get("/health/db")
async def db_health(session: AsyncDbSessionDep) -> dict:
    """Check that the database connection works."""
    result = await session.exec(select(1))
    result.one()
    return {"database": "up"}
