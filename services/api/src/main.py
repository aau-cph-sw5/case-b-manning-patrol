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

from src.services.event_producer import EventValidationError, TargetEventNotFoundError
from src.services.station_coverage.coverage_clock_tick import CoverageClockTick
from src.services.station_coverage.coverage_service import CoverageService
from src.services.station_coverage.coverage_updater import CoverageUpdater
from src.services.station_coverage.coverage_window import (
    MIN_QUALIFYING_DURATIONS,
    TIME_UNTIL_NEXT_NEEDED_PATROL,
    CoverageWindow,
)
from src.services.station_coverage.dashboard_presenter import DashboardPresenter
from src.services.station_coverage.interval_builder import IntervalBuilder
from src.services.station_coverage.overdue_tracker import OverdueTracker
from src.services.station_coverage.shift_schedule import ShiftSchedule
from src.services.station_coverage.sse_broadcaster import SseCoverageBroadcaster
from src.services.train_manning.train_manning_clock_tick import TrainManningClockTick
from src.services.train_manning.train_manning_evaluator import TrainManningEvaluator
from src.services.train_manning.train_manning_publisher import (
    SseTrainManningBroadcaster,
)
from src.services.train_manning.train_manning_service import TrainManningService
from src.services.train_manning.train_manning_updater import TrainManningUpdater

from .api.v2.routers import (
    adjustment,
    config,
    connection,
    dashboard_stream,
    health,
    patrol_session,
)
from .db.ingest import load_stations
from .db.main import engine, init_db
from .db.repository.station import get_station_lines, get_stations

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
        time_until_next_needed_patrol=TIME_UNTIL_NEXT_NEEDED_PATROL,
        min_qualifying_durations=MIN_QUALIFYING_DURATIONS,
    )
    shift_schedule = ShiftSchedule.from_file()
    sse_broadcaster = SseCoverageBroadcaster()
    overdue_tracker = OverdueTracker()
    service = CoverageService(builder, rule)
    coverage_updater = CoverageUpdater(
        service=service,
        tracker=overdue_tracker,
        publisher=sse_broadcaster,
        session_factory=lambda: AsyncSession(engine),
        clock=lambda: datetime.now(UTC),
        shift_schedule=shift_schedule,
    )
    train_manning_broadcaster = SseTrainManningBroadcaster()
    train_manning_updater = TrainManningUpdater(
        service=TrainManningService(builder, TrainManningEvaluator()),
        publisher=train_manning_broadcaster,
        session_factory=lambda: AsyncSession(engine),
        clock=lambda: datetime.now(UTC),
        shift_schedule=shift_schedule,
    )

    await coverage_updater.refresh()
    await train_manning_updater.refresh()
    coverage_tick = asyncio.create_task(
        CoverageClockTick(coverage_updater, timedelta(seconds=5)).run()
    )
    train_manning_tick = asyncio.create_task(
        TrainManningClockTick(train_manning_updater, timedelta(seconds=5)).run()
    )

    app.state.coverage_updater = coverage_updater
    app.state.sse_broadcaster = sse_broadcaster
    app.state.train_manning_updater = train_manning_updater
    app.state.train_manning_broadcaster = train_manning_broadcaster
    app.state.dashboard_presenter = dashboard_presenter

    yield
    coverage_tick.cancel()
    train_manning_tick.cancel()
    await engine.dispose()


app = FastAPI(title="Manning Patrol Backend", lifespan=lifespan)


@app.exception_handler(EventValidationError)
async def event_validation_exception_handler(
    _: Request,
    error: EventValidationError,
) -> JSONResponse:
    return JSONResponse(status_code=400, content={"code": "400", "message": str(error)})


@app.exception_handler(TargetEventNotFoundError)
async def target_event_not_found_exception_handler(
    _: Request,
    error: TargetEventNotFoundError,
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

app.include_router(adjustment.router, prefix=API_PREFIX_V2)
app.include_router(config.router, prefix=API_PREFIX_V2)
app.include_router(dashboard_stream.router, prefix=API_PREFIX_V2)
app.include_router(health.router, prefix=API_PREFIX_V2)
app.include_router(patrol_session.router, prefix=API_PREFIX_V2)
app.include_router(connection.router, prefix=API_PREFIX_V2)


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
