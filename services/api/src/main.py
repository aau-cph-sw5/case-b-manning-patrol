"""
Manning Patrol Backend

Main FastAPI application.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlmodel.ext.asyncio.session import AsyncSession

from src.services.producer import EventValidationError

from .api.v2.routers import adjustment, patrol_session
from .api.v1.routers import positioning_simulator
from .api.v2.routers import health, patrol_session
from .db.ingest import load_stations
from .db.main import engine, init_db

API_PREFIX_V1 = "/api/v1"
API_PREFIX_V2 = "/api/v2"


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    async with AsyncSession(engine) as session:
        await load_stations(session)
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
        content={"code": "400", "message": str(error)},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, error: RequestValidationError):
    return JSONResponse(status_code=400, content={"code": "400", "message": str(error)})


# CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(positioning_simulator.router, prefix=API_PREFIX_V1)
app.include_router(adjustment.router, prefix=API_PREFIX_V2)
app.include_router(health.router, prefix=API_PREFIX_V2)
app.include_router(patrol_session.router, prefix=API_PREFIX_V2)


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
