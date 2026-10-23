"""Tests for GET /api/v2/config/at-risk-threshold (AtRiskThreshold)."""


def test_at_risk_threshold_returns_200(client):
    response = client.get("/api/v2/config/at-risk-threshold")

    assert response.status_code == 200


def test_at_risk_threshold_returns_at_risk_threshold_secs(client):
    response = client.get("/api/v2/config/at-risk-threshold")

    body = response.json()
    assert isinstance(body["at_risk_threshold_secs"], int)
    assert body["at_risk_threshold_secs"] > 0


def test_at_risk_threshold_matches_contract_shape(client):
    response = client.get("/api/v2/config/at-risk-threshold")

    body = response.json()
    assert set(body.keys()) == {"at_risk_threshold_secs"}
