import os
from collections.abc import AsyncGenerator  # noqa: E402
from datetime import UTC, datetime

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402
from sqlmodel import SQLModel  # noqa: E402
from sqlmodel.ext.asyncio.session import AsyncSession  # noqa: E402

from src.api.v2.dependencies import get_async_db_session
from src.db.repository.station import get_station_lines, get_stations
from src.main import app
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
from src.services.train_manning.train_manning_evaluator import TrainManningEvaluator
from src.services.train_manning.train_manning_publisher import (
    SseTrainManningBroadcaster,
)
from src.services.train_manning.train_manning_service import TrainManningService
from src.services.train_manning.train_manning_updater import (
    TrainManningDeps,
    TrainManningUpdater,
)

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite://")


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


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

    app.state.coverage_updater = coverage_updater
    app.state.sse_broadcaster = sse_broadcaster
    app.state.train_manning_updater = train_manning_updater
    app.state.train_manning_broadcaster = train_manning_broadcaster
    app.state.dashboard_presenter = dashboard_presenter

    yield

    app.dependency_overrides.pop(get_async_db_session, None)
