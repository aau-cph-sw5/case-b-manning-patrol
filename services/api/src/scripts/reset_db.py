"""Reset the development database: drop all tables and re-run migrations."""

import asyncio

from sqlalchemy import text
from sqlmodel import SQLModel

from src.db.main import engine, upgrade_db


async def drop_tables() -> None:
    """Drop every model table and Alembic's version table."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
    await engine.dispose()


def main():
    """Run the reset against the database from DATABASE_URL."""
    asyncio.run(drop_tables())
    upgrade_db()
    print("Database reset: all tables dropped and migrations re-applied.")
    print("Start the server to re-ingest stations from the data file.")


if __name__ == "__main__":
    main()
