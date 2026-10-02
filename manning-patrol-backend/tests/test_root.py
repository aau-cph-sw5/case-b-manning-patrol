from fastapi.testclient import TestClient

from src.main import API_V1_PREFIX, app

client = TestClient(app)


def test_health_check():
    expected_response = {"status": "ok", "message": "Manning Patrol Backend running"}
    response = client.get(f"{API_V1_PREFIX}/health")
    assert response.status_code == 200
    assert response.json() == expected_response


def test_root():
    expected_response = {"message": "Hello"}
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == expected_response
