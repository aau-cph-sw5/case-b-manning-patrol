import os
import socket
import threading
import time
from collections.abc import AsyncGenerator, Generator  # noqa: E402
from datetime import UTC, datetime

import pytest
import pytest_asyncio
import uvicorn
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402
from sqlmodel import SQLModel  # noqa: E402
from sqlmodel.ext.asyncio.session import AsyncSession  # noqa: E402

from src.api.v2.dependencies import get_async_db_session
from src.api.v2.routers import connection, dashboard_stream, trains_stream
from src.db.repository.station import get_station_lines, get_stations
from src.db.repository.train import get_train_lines, get_trains
from src.main import app
from src.services.shared.interval_builder import IntervalBuilder
from src.services.shared.shift_schedule import ShiftSchedule
from src.services.station_coverage.coverage_service import CoverageService
from src.services.station_coverage.coverage_updater import CoverageUpdater
from src.services.station_coverage.coverage_window import (
    MIN_QUALIFYING_DURATIONS,
    TIME_UNTIL_NEXT_NEEDED_PATROL,
    CoverageWindow,
)
from src.services.station_coverage.dashboard_presenter import DashboardPresenter
from src.services.station_coverage.overdue_tracker import OverdueTracker
from src.services.station_coverage.sse_broadcaster import SseCoverageBroadcaster
from src.services.train_manning.train_manning_evaluator import TrainManningEvaluator
from src.services.train_manning.train_manning_publisher import (
    SseTrainManningBroadcaster,
)
from src.services.train_manning.train_manning_service import TrainManningService
from src.services.train_manning.train_manning_updater import (
    TrainManningDeps,
    TrainManningUpdater,
)
from src.services.train_manning.trains_update_presenter import TrainsUpdatePresenter

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite://")


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def live_base_url(override_db_session) -> Generator[str]:
    """Serve the real v2 routers over HTTP so SSE streams can be read live.

    TestClient buffers the whole response body, which never completes for an
    infinite SSE stream, so the stream endpoints need a real server. The
    served app shares the updaters, broadcasters, presenters and dependency
    overrides of the main app, so events POSTed through it reach the streams.
    """
    stream_app = FastAPI()
    for router in (connection.router, dashboard_stream.router, trains_stream.router):
        stream_app.include_router(router, prefix="/api/v2")
    for key in (
        "coverage_updater",
        "sse_broadcaster",
        "dashboard_presenter",
        "train_manning_updater",
        "train_manning_broadcaster",
        "trains_presenter",
    ):
        setattr(stream_app.state, key, getattr(app.state, key))
    stream_app.dependency_overrides = app.dependency_overrides

    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()

    server = uvicorn.Server(
        uvicorn.Config(stream_app, host="127.0.0.1", port=port, log_level="error")
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 10
    while not server.started and time.monotonic() < deadline:
        time.sleep(0.01)
    assert server.started, "test server did not start"

    yield f"http://127.0.0.1:{port}"

    server.should_exit = True
    thread.join(timeout=5)


@pytest_asyncio.fixture
async def db_engine() -> AsyncGenerator[AsyncEngine]:
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def override_db_session(db_engine: AsyncEngine) -> AsyncGenerator[None]:
    engine = db_engine

    async def get_test_session() -> AsyncGenerator[AsyncSession]:
        async with AsyncSession(engine, expire_on_commit=False) as session:
            yield session

    app.dependency_overrides[get_async_db_session] = get_test_session

    shift_schedule = ShiftSchedule.from_file()
    sse_broadcaster = SseCoverageBroadcaster()
    coverage_updater = CoverageUpdater(
        service=CoverageService(
            IntervalBuilder(),
            CoverageWindow(
                time_until_next_needed_patrol=TIME_UNTIL_NEXT_NEEDED_PATROL,
                min_qualifying_durations=MIN_QUALIFYING_DURATIONS,
            ),
        ),
        tracker=OverdueTracker(),
        publisher=sse_broadcaster,
        session_factory=lambda: AsyncSession(engine),
        clock=lambda: datetime.now(UTC),
        shift_schedule=shift_schedule,
    )
    train_manning_broadcaster = SseTrainManningBroadcaster()
    train_manning_updater = TrainManningUpdater(
        service=TrainManningService(IntervalBuilder(), TrainManningEvaluator()),
        publisher=train_manning_broadcaster,
        deps=TrainManningDeps(
            session_factory=lambda: AsyncSession(engine),
            clock=lambda: datetime.now(UTC),
            shift_schedule=shift_schedule,
        ),
    )

    async with AsyncSession(engine) as session:
        dashboard_presenter = DashboardPresenter(
            await get_stations(session), await get_station_lines(session)
        )
        trains_presenter = TrainsUpdatePresenter(
            await get_trains(session), await get_train_lines(session)
        )

    app.state.coverage_updater = coverage_updater
    app.state.sse_broadcaster = sse_broadcaster
    app.state.train_manning_updater = train_manning_updater
    app.state.train_manning_broadcaster = train_manning_broadcaster
    app.state.dashboard_presenter = dashboard_presenter
    app.state.trains_presenter = trains_presenter

    yield

    app.dependency_overrides.pop(get_async_db_session, None)
