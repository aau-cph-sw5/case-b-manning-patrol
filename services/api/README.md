# Manning Patrol Backend

Backend service for the Manning Patrol positioning system.

## Prerequisites

- Python 3.13
- [uv](https://github.com/astral-sh/uv) (Astral package manager)

## Running as a developer (step by step)

- Run `uv sync` — installs dependencies.
- Run `docker compose up -d` — starts the PostgreSQL container (port 5432 must be free).
- Create `services/api/.env` with `DATABASE_URL=postgresql+asyncpg://metro:admin@localhost:5432/metro` (see `.env-example`).
- Run `uv run alembic upgrade head` — applies migrations (before the first server start).
- Run `uv run dev` — starts the server with auto-reload on `http://localhost:8000`.

## Running in production (step by step)

- Run `uv sync --locked` — installs the locked dependencies (same as CI).
- Run `export DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:5432/DATABASE_NAME` — set it as a real environment variable, not a `.env` file.
- Run `uv run alembic upgrade head` — applies migrations against the production database.
- Run `uv run uvicorn src.main:app --host 0.0.0.0 --port 8000` — starts the server (no reload). Put a reverse proxy or process supervisor in front of it.

## Development

- Run `uv run check` — full CI check, run before pushing: `uv sync --locked`, `ruff check`, `ty check`, `ruff format --check`, `pytest`.
- Run `uv run lint` — lint + type check only: `ruff check src/ && ty check src/`.
- Run `uv run ruff check src/` — lint only.
- Run `uv run ty check src/` — type check only.
- Run `uv run ruff format .` — fix formatting before `check` complains.

CI also runs `alembic upgrade head` and `alembic check` against a PostgreSQL
service container, so a model change without a matching migration fails the
build (see [Migrations](#migrations)).

## Project Structure

```
services/api/
├── alembic/
│   ├── env.py                   # Reads DATABASE_URL and SQLModel metadata
│   └── versions/                # Migration scripts, applied in order
├── alembic.ini
├── src/
│   ├── main.py                  # FastAPI app definition and startup
│   ├── domain/                  # Pure value objects and enums (no storage or API imports)
│   │   ├── coverage.py          # Coverage and overdue log value objects (MET-B-007)
│   │   ├── event.py             # EventType and EventRecord
│   │   ├── patrol_area.py       # AreaKind
│   │   └── shift.py             # Shift
│   ├── db/
│   │   ├── models/              # SQLModel tables (events, adjustments, stations, areas, ...)
│   │   └── repository/          # Database query functions; overdue_log.py is the overdue log
│   ├── api/
│   │   └── v2/
│   │       ├── dependencies.py  # FastAPI dependencies (AsyncDbSessionDep, EventProducerDep)
│   │       ├── routers/
│   │       │   ├── adjustment.py       # Adjustment route (contracts/positioning-adjustment v2)
│   │       │   ├── config.py           # At-risk threshold config
│   │       │   ├── connection.py       # Connection ingestion routes (contracts/positioning-ingestion v2)
│   │       │   ├── dashboard_stream.py # SSE dashboard stream (contracts/positioning-interface v2)
│   │       │   ├── health.py           # Health check endpoints (contracts/health v2)
│   │       │   └── patrol_session.py   # Patrol-session ingestion routes (contracts/positioning-ingestion v2)
│   │       └── schemas/         # Request/response payloads (dashboard, adjustment, ingestion)
│   ├── scripts/                 # `uv run lint` / `uv run check` entry points
│   └── services/
│       ├── event_producer.py    # Appends events/adjustments to the append-only store
│       ├── positioning_service.py
│       └── station_coverage/    # Patrol coverage computation, overdue tracking and SSE publishing (MET-B-007)
├── fixtures/
│   └── fixture-events-v1.json   # Event timeline inserted by the seed script
├── tests/
├── docker-compose.yml # Local PostgreSQL database for development
├── pyproject.toml    # Dependencies and tool config
├── uv.lock           # Locked dependency versions
└── .python-version   # Python version (3.13)
```

## Database

The backend uses PostgreSQL through SQLModel and the async `asyncpg` driver.
See [Running as a developer](#running-as-a-developer-step-by-step) for the
full setup: `docker-compose.yml` defines the local PostgreSQL container
(fixed credentials `metro` / `admin`, port 5432), and `.env-example` shows the
`DATABASE_URL` format.

- `src/db/config.py` reads `DATABASE_URL` from the environment or the `.env`
  file. Alembic reads the same setting, so `alembic.ini` holds no database
  URL. Without `DATABASE_URL` the app falls back to a local SQLite file
  (`local.db`).
- The schema is managed by Alembic migrations in `alembic/versions/`.
- `src/db/main.py` creates the engine and still runs `create_all` on server
  startup. Apply migrations before starting the server on a new database,
  otherwise the tables are created without Alembic's version record and
  `alembic upgrade head` will fail with "table already exists".
- `src/db/ingest.py` then loads `src/data/stations.v1.json` into those tables.
  It replaces their contents on every start, so rows added by hand are lost.
  See `src/data/README.md`.
- `src/db/` — holds the database access layer (connection setup, tables,
  queries).

### Migrations

- Run `uv run alembic upgrade head` — apply migrations (after pulling changes).
- After changing a table in `src/db/models/`, generate a migration, read it, and commit it with the model change:

  ```bash
  uv run alembic revision --autogenerate -m "describe the change"
  uv run alembic upgrade head
  uv run alembic check    # passes when the models and migrations agree
  ```

  Note: autogenerate compares against your current database, so run
  `upgrade head` first. Review the generated file: it does not detect renames
  (it emits a drop and an add, losing data), and adding a `nullable=False`
  column to a table with rows needs a default or a backfill.

### Seeding

- Run `uv run python -m src.scripts.seed` — applies pending migrations, then inserts the fixture event timeline (only inserts rows that are missing).

### Resetting the database

- Run `uv run reset-db` — drops every table (including `alembic_version`) and re-applies all migrations. Stations, lines and patrol areas are re-ingested on the next server start; other rows (events, adjustments) are lost. Use `docker compose down -v` to start completely fresh.
