"""Tests for the at-risk threshold config endpoints (AtRiskThreshold)."""

from src.models.config import DEFAULT_AT_RISK_THRESHOLD_MINUTES


def test_at_risk_threshold_returns_200(client):
    response = client.get("/api/v2/config/at-risk-threshold")

    assert response.status_code == 200


def test_at_risk_threshold_returns_default_minutes(client):
    response = client.get("/api/v2/config/at-risk-threshold")

    body = response.json()
    assert body["at_risk_threshold_minutes"] == DEFAULT_AT_RISK_THRESHOLD_MINUTES


def test_at_risk_threshold_matches_contract_shape(client):
    response = client.get("/api/v2/config/at-risk-threshold")

    body = response.json()
    assert set(body.keys()) == {"at_risk_threshold_minutes"}
    assert isinstance(body["at_risk_threshold_minutes"], int)
    assert body["at_risk_threshold_minutes"] > 0


def test_post_updates_threshold(client):
    response = client.post(
        "/api/v2/config/at-risk-threshold",
        json={"at_risk_threshold_minutes": 15},
    )

    assert response.status_code == 200
    assert response.json() == {"at_risk_threshold_minutes": 15}


def test_post_persists_update(client):
    client.post(
        "/api/v2/config/at-risk-threshold",
        json={"at_risk_threshold_minutes": 15},
    )

    response = client.get("/api/v2/config/at-risk-threshold")
    assert response.json() == {"at_risk_threshold_minutes": 15}


def test_post_rejects_value_below_contract_minimum(client):
    response = client.post(
        "/api/v2/config/at-risk-threshold",
        json={"at_risk_threshold_minutes": 0},
    )

    assert response.status_code == 400
