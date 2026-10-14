"""Reset the development database: drop and recreate all tables."""

import asyncio

from sqlmodel import SQLModel

from src.db.main import engine, init_db


async def reset_db() -> None:
    """Drop every table, then recreate them from the current models."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await init_db()
    await engine.dispose()


def main():
    """Run the reset against the database from DATABASE_URL."""
    asyncio.run(reset_db())
    print("Database reset: all tables dropped and recreated.")
    print("Start the server to re-ingest stations from the data file.")


if __name__ == "__main__":
    main()
