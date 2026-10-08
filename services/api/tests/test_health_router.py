import pytest

from src.main import health_check


@pytest.mark.asyncio
async def test_health_check():
    health_response = {"status": "ok", "message": "Manning Patrol Backend running"}
    health_call = await health_check()
    assert health_call == health_response
