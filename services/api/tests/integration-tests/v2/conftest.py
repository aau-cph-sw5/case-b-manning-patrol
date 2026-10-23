import os
from collections.abc import AsyncGenerator  # noqa: E402
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402
from sqlmodel import SQLModel  # noqa: E402
from sqlmodel.ext.asyncio.session import AsyncSession  # noqa: E402

from src.db.main import get_session
from src.db.repository.station import get_station_lines, get_stations
from src.main import app
from src.models.patrol_area import AreaKind
from src.services.coverage.coverage_service import CoverageService
from src.services.coverage.coverage_updater import CoverageUpdater
from src.services.coverage.coverage_window import CoverageWindow
from src.services.coverage.dashboard_presenter import DashboardPresenter
from src.services.coverage.interval_builder import IntervalBuilder
from src.services.coverage.shift_schedule import ShiftSchedule
from src.services.coverage.sse_broadcaster import SseBroadcaster
from src.services.overdue_tracker import OverdueTracker

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite://")


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest_asyncio.fixture(autouse=True)
async def override_db_session() -> AsyncGenerator[None]:
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async def get_test_session() -> AsyncGenerator[AsyncSession]:
        async with AsyncSession(engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_test_session

    sse_broadcaster = SseBroadcaster()
    coverage_updater = CoverageUpdater(
        service=CoverageService(
            IntervalBuilder(),
            CoverageWindow(
                time_until_next_needed_patrol=timedelta(minutes=60),
                min_qualifying_durations={
                    AreaKind.PLATFORM: timedelta(seconds=4),
                    AreaKind.CONCOURSE: timedelta(minutes=10),
                },
            ),
        ),
        tracker=OverdueTracker(),
        publisher=sse_broadcaster,
        session_factory=lambda: AsyncSession(engine),
        clock=lambda: datetime.now(UTC),
        shift_schedule=ShiftSchedule.from_file(),
    )

    async with AsyncSession(engine) as session:
        dashboard_presenter = DashboardPresenter(
            await get_stations(session), await get_station_lines(session)
        )

    app.state.coverage_updater = coverage_updater
    app.state.sse_broadcaster = sse_broadcaster
    app.state.dashboard_presenter = dashboard_presenter

    yield

    app.dependency_overrides.pop(get_session, None)
    await engine.dispose()
