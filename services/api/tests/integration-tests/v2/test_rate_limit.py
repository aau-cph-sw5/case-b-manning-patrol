from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from src.api.limiter import limiter
from src.main import app

LIMIT_PER_MINUTE = 120


@pytest.fixture
def limited_client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setattr(limiter, "enabled", True)
    limiter.reset()
    yield TestClient(app)
    limiter.reset()


def test_v2_endpoint_answers_429_after_limit(limited_client: TestClient) -> None:
    for _ in range(LIMIT_PER_MINUTE):
        assert limited_client.get("/api/v2/health").status_code == 200

    response = limited_client.get("/api/v2/health")

    assert response.status_code == 429
    assert response.headers["Retry-After"]


def test_v2_endpoint_reports_remaining_requests(limited_client: TestClient) -> None:
    response = limited_client.get("/api/v2/health")

    assert response.headers["X-RateLimit-Limit"] == str(LIMIT_PER_MINUTE)
    assert response.headers["X-RateLimit-Remaining"] == str(LIMIT_PER_MINUTE - 1)


def test_limits_are_counted_per_endpoint(limited_client: TestClient) -> None:
    for _ in range(LIMIT_PER_MINUTE):
        limited_client.get("/api/v2/health")

    assert limited_client.get("/ping").status_code == 200


def test_limiter_is_disabled_in_tests() -> None:
    assert limiter.enabled is False
