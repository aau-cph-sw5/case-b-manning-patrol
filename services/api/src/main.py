"""
Manning Patrol Backend

Main FastAPI application.
"""

import asyncio
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.patrol_area import AreaKind
from src.services.coverage.coverage_service import CoverageService
from src.services.coverage.coverage_updater import ClockTick, CoverageUpdater
from src.services.coverage.coverage_window import CoverageWindow
from src.services.coverage.dashboard_presenter import DashboardPresenter
from src.services.coverage.interval_builder import IntervalBuilder
from src.services.coverage.shift_schedule import ShiftSchedule
from src.services.coverage.sse_broadcaster import SseBroadcaster
from src.services.overdue_tracker import OverdueTracker
from src.services.producer import EventValidationError

from .api.v1.routers import positioning_simulator
from .api.v2.routers import adjustment, config, dashboard_stream, health, patrol_session
from .db.ingest import load_stations
from .db.main import engine, init_db
from .db.repository.station import get_station_lines, get_stations

API_PREFIX_V1 = "/api/v1"
API_PREFIX_V2 = "/api/v2"


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    async with AsyncSession(engine) as session:
        await load_stations(session)
        dashboard_presenter = DashboardPresenter(
            await get_stations(session), await get_station_lines(session)
        )

    builder = IntervalBuilder()
    rule = CoverageWindow(
        time_until_next_needed_patrol=timedelta(minutes=60),
        min_qualifying_durations={
            AreaKind.PLATFORM: timedelta(seconds=4),
            AreaKind.CONCOURSE: timedelta(minutes=10),
        },
    )
    sse_broadcaster = SseBroadcaster()
    overdue_tracker = OverdueTracker()
    service = CoverageService(builder, rule)
    coverage_updater = CoverageUpdater(
        service=service,
        tracker=overdue_tracker,
        publisher=sse_broadcaster,
        session_factory=lambda: AsyncSession(engine),
        clock=lambda: datetime.now(UTC),
        shift_schedule=ShiftSchedule.from_file(),
    )

    await coverage_updater.refresh()
    tick = asyncio.create_task(ClockTick(coverage_updater, timedelta(seconds=5)).run())

    app.state.coverage_updater = coverage_updater
    app.state.sse_broadcaster = sse_broadcaster
    app.state.dashboard_presenter = dashboard_presenter

    yield
    tick.cancel()
    await engine.dispose()


app = FastAPI(title="Manning Patrol Backend", lifespan=lifespan)


@app.exception_handler(EventValidationError)
async def event_validation_exception_handler(
    _: Request,
    error: EventValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"code": "404", "message": str(error)},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, error: RequestValidationError):
    return JSONResponse(status_code=400, content={"code": "400", "message": str(error)})


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(positioning_simulator.router, prefix=API_PREFIX_V1)
app.include_router(adjustment.router, prefix=API_PREFIX_V2)
app.include_router(config.router, prefix=API_PREFIX_V2)
app.include_router(dashboard_stream.router, prefix=API_PREFIX_V2)
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
