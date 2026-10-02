import pytest

from src.main import health_check, hello


@pytest.mark.asyncio
async def test_health_check():
    expected_response = {"status": "ok", "message": "Manning Patrol Backend running"}
    actual_response = await health_check()
    assert actual_response == expected_response


@pytest.mark.asyncio
async def test_root():
    expected_response = {"message": "Hello"}
    actual_response = await hello()
    assert actual_response == expected_response
