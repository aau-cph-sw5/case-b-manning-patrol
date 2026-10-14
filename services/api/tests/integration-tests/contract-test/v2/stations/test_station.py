"""Tests for GET /api/v2/stations/{stationID} (StationResponse)."""

from datetime import datetime
from uuid import UUID

UNKNOWN_STATION_ID = "880e8400-e29b-41d4-a716-446655440099"


def test_get_station_returns_station(client, seeded_station_id):
    dashboard_response = client.get("/api/v2/dashboard")
    assert dashboard_response.status_code == 200
    station_id = dashboard_response.json()["stations"][0]["station_id"]

    response = client.get(f"/api/v2/stations/{station_id}")

    assert response.status_code == 200
    station = response.json()
    assert station["station_id"] == station_id
    assert isinstance(station["slug"], str)
    assert isinstance(station["areas"], list)
    for area in station["areas"]:
        assert UUID(area["beacon_id"])
        assert isinstance(area["slug"], str)
        assert datetime.fromisoformat(area["last_manned_at"])
        steward = area["current_steward_id"]
        assert steward is None or UUID(steward)


def test_get_unknown_station_returns_404(client):
    response = client.get(f"/api/v2/stations/{UNKNOWN_STATION_ID}")

    assert response.status_code == 404
    error = response.json()
    assert isinstance(error["code"], str)
    assert isinstance(error["message"], str)
