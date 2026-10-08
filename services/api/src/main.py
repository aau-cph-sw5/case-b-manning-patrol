"""
Manning Patrol Backend

Main FastAPI application.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.services.producer import EventValidationError

from .api.v1.routers import events, health, positioning_simulator
from .db.main import engine, init_db

API_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await engine.dispose()


app = FastAPI(title="Manning Patrol Backend", lifespan=lifespan)


@app.exception_handler(EventValidationError)
async def event_validation_exception_handler(
    _: Request,
    error: EventValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"detail": str(error)},
    )


# CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix=API_PREFIX)
app.include_router(positioning_simulator.router, prefix=API_PREFIX)
app.include_router(events.router, prefix=API_PREFIX)


@app.get("/ping")
async def ping():
    return {"message": "up"}


@app.get("/")
def hello():
    """Stub endpoint for root path"""
    return {"message": "Hello"}


def dev():
    """Run development server with reload."""
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
