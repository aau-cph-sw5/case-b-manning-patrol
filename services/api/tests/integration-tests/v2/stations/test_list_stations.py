"""Tests for GET /api/v2/stations (station list for the web dashboard)."""

from uuid import UUID

SEEDED_BEACON_ID = "550e8400-e29b-41d4-a716-446655440000"


def test_list_stations_returns_seeded_station(client, seeded_station_id):
    """Test that the /api/v2/stations endpoint returns
    the seeded station and its patrol area."""
    response = client.get("/api/v2/stations")

    assert response.status_code == 200
    stations = response.json()
    assert len(stations) == 1
    assert stations[0]["id"] == "STN-001"
    assert stations[0]["name"] == "Station 01"

    assert len(stations[0]["patrol_areas"]) == 1
    area = stations[0]["patrol_areas"][0]
    assert area["kind"] == "platform"
    assert area["beacon_id"] == SEEDED_BEACON_ID


def test_list_stations_validates_beacon_id_format(client, seeded_station_id):
    """Test that the /api/v2/stations endpoint returns
    a valid UUID for the beacon_id field."""
    response = client.get("/api/v2/stations")

    assert response.status_code == 200
    stations = response.json()
    for station in stations:
        for area in station["patrol_areas"]:
            assert UUID(area["beacon_id"])


def test_list_stations_empty_db_returns_empty_list(client):
    """Test that the /api/v2/stations endpoint returns
    an empty list when there are no stations in the database."""
    response = client.get("/api/v2/stations")

    assert response.status_code == 200
    assert response.json() == []
