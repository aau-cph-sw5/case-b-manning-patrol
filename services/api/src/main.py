"""
Manning Patrol Backend

Main FastAPI application.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.v1.routers import health, positioning_ingestion, positioning_simulator
from src.api.v2.routers import positioning_ingestion as positioning_ingestion_v2

API_PREFIX = "/api/v1"
API_V2_PREFIX = "/api/v2"

app = FastAPI(title="Manning Patrol Backend")

# CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix=API_PREFIX)
app.include_router(positioning_ingestion.router, prefix=API_PREFIX)
app.include_router(positioning_simulator.router, prefix=API_PREFIX)
app.include_router(positioning_ingestion_v2.router, prefix=API_V2_PREFIX)


@app.get("/")
def hello():
    """Stub endpoint for root path"""
    return {"message": "Hello"}


def dev():
    """Run development server with reload."""
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
