"""Tests for GET /api/v2/dashboard (DashboardResponse).

from datetime import datetime
from uuid import UUID


def test_dashboard_returns_stations_and_trains(client, seeded_station_id):
    response = client.get("/api/v2/dashboard")

    assert response.status_code == 200
    dashboard = response.json()
    assert isinstance(dashboard["stations"], list)
    assert isinstance(dashboard["trains"], list)
    assert len(dashboard["stations"]) >= 1
    for station in dashboard["stations"]:
        assert UUID(station["station_id"])
        assert isinstance(station["slug"], str)
        assert isinstance(station["areas"], list)
        for area in station["areas"]:
            assert UUID(area["beacon_id"])
            assert isinstance(area["slug"], str)
            assert datetime.fromisoformat(area["last_manned_at"])
            steward = area["current_steward_id"]
            assert steward is None or UUID(steward)
    for train in dashboard["trains"]:
        assert UUID(train["train_id"])
        assert isinstance(train["slug"], str)
        assert isinstance(train["total_time_secs"], int)
        assert isinstance(train["manned_time_secs"], int)
        steward = train["current_steward_id"]
        assert steward is None or UUID(steward)
"""
