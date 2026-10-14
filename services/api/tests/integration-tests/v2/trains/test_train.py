"""Tests for GET /api/v2/trains/{trainID} (TrainResponse).

UNKNOWN_TRAIN_ID = "770e8400-e29b-41d4-a716-446655440099"


def test_get_unknown_train_returns_404(client):
    response = client.get(f"/api/v2/trains/{UNKNOWN_TRAIN_ID}")

    assert response.status_code == 404
    error = response.json()
    assert isinstance(error["code"], str)
    assert isinstance(error["message"], str)
"""
