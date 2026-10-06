import httpx

from src.db.main import get_session, init_db


async def test_init_db_creates_tables(engine):
    await init_db(engine)

    async with engine.connect() as conn:
        result = await conn.exec_driver_sql(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = {row[0] for row in result}

    assert "station" in tables
    assert "patrolarea" in tables


async def test_get_session_via_endpoint(engine, session_factory, app):
    await init_db(engine)
    app.dependency_overrides[get_session] = session_factory

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health/db")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["database"] == "up"
