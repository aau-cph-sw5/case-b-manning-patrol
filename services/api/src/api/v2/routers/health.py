"""
Health

Health check endpoint for the backend.
"""

from fastapi import APIRouter
from sqlmodel import select

from src.db.main import SessionDep

router = APIRouter(tags=["health"])


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
