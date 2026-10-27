"""Tests for the Health API contract (HealthStatus, DatabaseHealthStatus)."""

EXPECTED_HEALTH = {"status": "ok", "message": "Manning Patrol Backend running"}
EXPECTED_DATABASE_HEALTH = {"database": "up"}


def test_health_check(client):
    response = client.get("/api/v2/health")

    assert response.status_code == 200
    assert response.json() == EXPECTED_HEALTH


def test_health_db_check(client):
    response = client.get("/api/v2/health/db")

    assert response.status_code == 200
    assert response.json() == EXPECTED_DATABASE_HEALTH
