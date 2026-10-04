"""
Manning Patrol Backend

Main FastAPI application.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.services.db import init_db
from src.api.v1.routers.events import router as events_router

from src.api.v1.routers import health, positioning_simulator

API_PREFIX = "/api/v1"

app = FastAPI(title="Manning Patrol Backend")

# Initialize local database
init_db()

# CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix=API_PREFIX)
app.include_router(positioning_simulator.router, prefix=API_PREFIX)
app.include_router(events_router, prefix=API_PREFIX)

@app.get("/")
def hello():
    """Stub endpoint for root path"""
    return {"message": "Hello"}


def dev():
    """Run development server with reload."""
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
