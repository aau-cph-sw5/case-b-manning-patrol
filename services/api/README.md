# Manning Patrol Backend

Backend service for the Manning Patrol positioning system.

## Prerequisites

- Python 3.13
- [uv](https://github.com/astral-sh/uv) (Astral package manager)

## Running as a developer (step by step)

- Run `uv sync` — installs dependencies.
- Run `docker compose up -d` — starts the PostgreSQL container. 
- Create `services/api/.env` with `DATABASE_URL=postgresql+asyncpg://metro:admin@localhost:5432/metro` — the Compose credentials are fixed (see `.env-example`). Without `DATABASE_URL` the app falls back to a local SQLite file (`local.db`).
- Run `uv run alembic upgrade head` — applies migrations. Do this before the first server start.
- Run `uv run dev` — starts the server with auto-reload on `http://localhost:8000`.


## Running in production (step by step)

- Install the locked dependencies (same command CI uses):

  ```bash
  uv sync --locked
  ```

- Provide `DATABASE_URL` as a real environment variable on the host — do not
  rely on a `.env` file in production (if one exists in the working
  directory it is read too):

  ```bash
  export DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:5432/DATABASE_NAME
  ```

- Apply database migrations against the production database:

  ```bash
  uv run alembic upgrade head
  ```

- Start the server with uvicorn directly — no reload, bound to all
  interfaces:

  ```bash
  uv run uvicorn src.main:app --host 0.0.0.0 --port 8000
  ```

  Note: put a reverse proxy (or process supervisor) in front of it; uvicorn
  is not a service manager. The same startup sequence as in development
  runs: tables are ensured, stations/lines/patrol areas are re-ingested, and
  the coverage updater starts ticking every 5 seconds.

## Development

### Lint + Type Check (one command)

```bash
uv run lint
```

This runs `ruff check src/ && ty check src/`

### Full CI check (run before pushing)

```bash
uv run check
```

This runs the same steps as CI: `uv sync --locked`, `ruff check`, `ty check`, `ruff format --check`, and `pytest`.

CI additionally runs `alembic upgrade head` and `alembic check` against a
PostgreSQL service container, so a model change without a matching migration
fails the build. Run them locally against your database before pushing a
model change (see [Migrations](#migrations)).

### Individual commands

```bash
# Lint only
uv run ruff check src/

# Type check only
uv run ty check src/
```

## Project Structure

```
services/api/
├── alembic/
│   ├── env.py                   # Reads DATABASE_URL and SQLModel metadata
│   └── versions/                # Migration scripts, applied in order
├── alembic.ini
├── src/
│   ├── main.py                  # FastAPI app definition and startup
│   ├── models/                  # Shared models (events, adjustments, beacons)
│   │   ├── coverage.py          # Coverage and overdue log value objects (MET-B-007, skeleton)
│   │   └── dashboard.py         # Dashboard stream payload (contracts/positioning-interface v2)
│   ├── db/repository/           # Database query functions; overdue_log.py is the overdue log (skeleton)
│   ├── api/
│   │   ├── v1/
│   │   │   └── routers/
│   │   │       ├── adjustment.py       # Adjustment route (contracts/positioning-adjustment v1, draft)
│   │   │       ├── health.py           # Health check endpoint
│   │   │       └── positioning_simulator.py # Positioning Interface simulator
│   │   └── v2/
│   │       └── routers/
│   │           ├── patrol_session.py   # Connection and patrol-session ingestion routes (contracts/positioning-ingestion v2)
│   │           └── dashboard_stream.py # SSE dashboard stream (contracts/positioning-interface v2)
│   ├── scripts/                 # `uv run lint` / `uv run check` entry points
│   └── services/
│       ├── coverage/            # Patrol coverage computation, overdue tracking and SSE publishing (MET-B-007, skeleton)
│       ├── positioning_service.py
│       ├── db/                  # Empty
│       └── producer.py          # Event/adjustment producer
├── fixtures/
│   └── fixture-events-v1.json   # Event timeline replayed by the simulator
├── tests/
├── docker-compose.yml # Local PostgreSQL database for development
├── pyproject.toml    # Dependencies and tool config
├── uv.lock           # Locked dependency versions
└── .python-version   # Python version (3.13)
```

## Positioning Simulator

Implements the Positioning Interface contract (`contracts/positioning-interface/v1/`):

- `GET /observations` - Returns currently active area observations
- `GET /observation-events` - Returns all observation events
- `GET /ws/observation-events` - WebSocket stream of events

Fixture used:
- `fixtures/fixture-events-v1.json` - Event timeline replayed by the simulator

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
- `src/services/db/` — holds the database access layer (connection
  setup, queries).

### Migrations

After pulling changes, bring your database up to date:

```bash
uv run alembic upgrade head
```

After changing a model in `src/models/`, generate a migration, read it, and
commit it with the model change:

```bash
uv run alembic revision --autogenerate -m "describe the change"
uv run alembic upgrade head
uv run alembic check    # passes when the models and migrations agree
```

Autogenerate compares the models against your current database, so run
`upgrade head` first, otherwise the migration also contains changes that are
already in earlier migrations. Review the generated file: autogenerate does not
detect renames (it emits a drop and an add, losing data) and adding a
`nullable=False` column to a table with rows needs a default or a backfill.

### Seeding

```bash
uv run python -m src.scripts.seed
```

Applies pending migrations, then inserts the fixture event timeline. Running it
again only inserts rows that are missing.

### Resetting the database

If your database is in a state migrations cannot fix (for example, tables
created by an older server start before Alembic), reset it with:

```bash
uv run reset-db
```

This drops every table, including Alembic's `alembic_version`, and re-applies
all migrations. Stations, lines and patrol areas are re-ingested from
`src/data/stations.v1.json` on the next server start, but any other rows
(events, adjustments) are lost. Tables that no longer exist in the models are
not dropped; use `docker compose down -v` to start completely fresh.

## Tool Configuration

- **uv**: Package management
- **ruff**: Linter (E/F/I/N/W/UP rules, line-length 88)
- **ty**: Type checker (from Astral)
