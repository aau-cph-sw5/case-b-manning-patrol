"""
Health

Health check endpoint for the backend.
"""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "message": "Manning Patrol Backend running"}
